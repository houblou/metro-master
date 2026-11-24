"""Interface en ligne de commande de MetrologyLab AI."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

from . import __version__
from .agents import compose_prompt, list_agents
from .execution import BUILTIN_OPERATIONS, CalculationRequest, DeterministicEngine
from .knowledge import KnowledgeStore
from .library import DocumentLibrary
from .module_registry import ModuleStore
from .orchestrator import MetroOrchestrator
from .pdf_library import GovernedPdfLibrary, MAX_PAGES_PER_CHUNK
from .rag import HybridRagRetriever
from .reporting import REPORT_KINDS, render_study_report
from .study_history import StudyStore
from .token_budget import TokenBudgetPolicy
from .uncertainty_oracles import verify_with_external_oracles
from .uncertainty_study import build_uncertainty_study


def _configure_utf8_streams() -> None:
    """Use UTF-8 for redirected CLI output while preserving interactive consoles."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not stream.isatty() and callable(reconfigure):
            reconfigure(encoding="utf-8")


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _dump(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _write_trace(path: str | None, record: object) -> None:
    if path is None:
        return
    trace = getattr(record, "trace", None)
    if trace is None:
        raise ValueError("calculation record has no trace")
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"trace output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(trace.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_new_text(path: str | None, value: str, *, label: str) -> None:
    if path is None:
        return
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"{label} output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(value, encoding="utf-8")


def _parser(prog: str = "metro-master") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="MetrologyLab AI — métrologie multi-agents et calculs vérifiables",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("agents", help="lister les agents")

    prompt = sub.add_parser("prompt", help="composer le prompt complet d'un agent")
    prompt.add_argument("agent")
    prompt.add_argument(
        "--token-mode",
        choices=("eco", "standard", "deep"),
        default="standard",
    )

    route = sub.add_parser("route", help="afficher le plan d'orchestration")
    route.add_argument("request")

    token_plan = sub.add_parser(
        "token-plan",
        help="afficher le routage limite par un profil de tokens",
    )
    token_plan.add_argument("request")
    token_plan.add_argument(
        "--mode",
        default="standard",
        help="profil du fichier de configuration (eco, standard, deep ou personnalisé)",
    )
    token_plan.add_argument("--config")

    library = sub.add_parser("library", help="interroger le catalogue documentaire")
    library.add_argument("--query", default="")
    library.add_argument("--publisher", default="")
    library.add_argument("--catalog")

    pdf_search = sub.add_parser(
        "pdf-search", help="interroger le manifeste de la bibliothèque PDF gouvernée"
    )
    pdf_search.add_argument("--query", default="")
    pdf_search.add_argument("--sources", default="library/source-roots.json")
    pdf_search.add_argument("--source-id")

    pdf_extract = sub.add_parser(
        "pdf-extract", help="extraire un lot paginé d'un PDF gouverné"
    )
    pdf_extract.add_argument("record_id")
    pdf_extract.add_argument("--sources", default="library/source-roots.json")
    pdf_extract.add_argument("--source-id")
    pdf_extract.add_argument("--chunk", type=int, default=1)
    pdf_extract.add_argument("--chunk-size", type=int, default=MAX_PAGES_PER_CHUNK)

    budget = sub.add_parser("budget", help="calculer un budget JSON")
    budget.add_argument("input")
    budget.add_argument("--trace-out")

    compare = sub.add_parser("compare", help="calculer un écart corrélé JSON")
    compare.add_argument("input")
    compare.add_argument("--trace-out")

    paired = sub.add_parser("paired", help="analyser des lectures appariées JSON")
    paired.add_argument("input")
    paired.add_argument("--trace-out")

    separate = sub.add_parser(
        "separate", help="séparer conditionnellement l'incertitude du banc"
    )
    separate.add_argument("input")
    separate.add_argument("--trace-out")

    uncertainty_study = sub.add_parser(
        "uncertainty-study",
        help="exécuter le parcours GUM en quatre étapes et produire une note LaTeX",
    )
    uncertainty_study.add_argument("input")
    uncertainty_study.add_argument("--trace-out")
    uncertainty_study.add_argument("--note-out")

    uncertainty_verify = sub.add_parser(
        "uncertainty-verify",
        help="contre-vérifier un bilan avec les bibliothèques optionnelles",
    )
    uncertainty_verify.add_argument("input")

    module_list = sub.add_parser(
        "module-list", help="lister les modules natifs et les modules gouvernés"
    )
    module_list.add_argument("--root", default="modules/registry")

    module_submit = sub.add_parser(
        "module-submit", help="soumettre un manifeste comme module candidat"
    )
    module_submit.add_argument("manifest")
    module_submit.add_argument("--created-by", required=True)
    module_submit.add_argument("--root", default="modules/registry")

    module_test = sub.add_parser(
        "module-test", help="exécuter les cas de référence d'un module"
    )
    module_test.add_argument("module_id")
    module_test.add_argument("version")
    module_test.add_argument("--root", default="modules/registry")

    module_promote = sub.add_parser(
        "module-promote", help="promouvoir un candidat validé après approbation humaine"
    )
    module_promote.add_argument("module_id")
    module_promote.add_argument("version")
    module_promote.add_argument("--approved-by", required=True)
    module_promote.add_argument("--root", default="modules/registry")

    module_deprecate = sub.add_parser(
        "module-deprecate", help="déprécier une version validée"
    )
    module_deprecate.add_argument("module_id")
    module_deprecate.add_argument("version")
    module_deprecate.add_argument("--approved-by", required=True)
    module_deprecate.add_argument("--reason", required=True)
    module_deprecate.add_argument("--root", default="modules/registry")

    module_rollback = sub.add_parser(
        "module-rollback", help="réactiver une version validée antérieure"
    )
    module_rollback.add_argument("module_id")
    module_rollback.add_argument("version")
    module_rollback.add_argument("--approved-by", required=True)
    module_rollback.add_argument("--root", default="modules/registry")

    module_run = sub.add_parser(
        "module-run", help="exécuter un module validé ou natif"
    )
    module_run.add_argument("module_id")
    module_run.add_argument("input")
    module_run.add_argument("--root", default="modules/registry")
    module_run.add_argument("--trace-out")

    knowledge_list = sub.add_parser(
        "knowledge-list", help="lister la mémoire locale gouvernée"
    )
    knowledge_list.add_argument("--root", default="knowledge/registry")

    knowledge_search = sub.add_parser(
        "knowledge-search", help="rechercher dans les connaissances mémorisées"
    )
    knowledge_search.add_argument("query")
    knowledge_search.add_argument("--root", default="knowledge/registry")
    knowledge_search.add_argument("--include-candidates", action="store_true")
    knowledge_search.add_argument("--limit", type=int, default=5)
    knowledge_search.add_argument(
        "--mode", choices=("hybrid", "lexical"), default="hybrid"
    )

    knowledge_promote = sub.add_parser(
        "knowledge-promote",
        help="valider humainement une connaissance candidate",
    )
    knowledge_promote.add_argument("knowledge_id")
    knowledge_promote.add_argument("--approved-by", required=True)
    knowledge_promote.add_argument("--reason", required=True)
    knowledge_promote.add_argument("--root", default="knowledge/registry")

    knowledge_supersede = sub.add_parser(
        "knowledge-supersede",
        help="retirer une connaissance devenue fausse ou périmée",
    )
    knowledge_supersede.add_argument("knowledge_id")
    knowledge_supersede.add_argument("--approved-by", required=True)
    knowledge_supersede.add_argument("--reason", required=True)
    knowledge_supersede.add_argument("--root", default="knowledge/registry")

    study_list = sub.add_parser(
        "study-list", help="lister l'historique persistant des études"
    )
    study_list.add_argument("--root", default="studies/registry")

    study_show = sub.add_parser(
        "study-show", help="afficher une révision d'étude et vérifier sa chaîne"
    )
    study_show.add_argument("study_id")
    study_show.add_argument("--revision", type=int)
    study_show.add_argument("--root", default="studies/registry")

    study_export = sub.add_parser(
        "study-export", help="exporter un rapport ou projet non officiel"
    )
    study_export.add_argument("study_id")
    study_export.add_argument("--revision", type=int)
    study_export.add_argument("--kind", choices=sorted(REPORT_KINDS), required=True)
    study_export.add_argument("--output", required=True)
    study_export.add_argument("--organization", default="[organisme à renseigner]")
    study_export.add_argument("--prepared-by", default="[préparateur à renseigner]")
    study_export.add_argument("--root", default="studies/registry")
    return parser


def main(argv: list[str] | None = None, *, prog: str = "metro-master") -> int:
    _configure_utf8_streams()
    args = _parser(prog).parse_args(argv)
    engine = DeterministicEngine()
    try:
        if args.command == "agents":
            _dump([{"name": item.name, "description": item.description} for item in list_agents()])
        elif args.command == "prompt":
            print(compose_prompt(args.agent, TokenBudgetPolicy.load(args.token_mode)))
        elif args.command == "route":
            _dump(MetroOrchestrator().plan(args.request).to_dict())
        elif args.command == "token-plan":
            policy = TokenBudgetPolicy.load(args.mode, args.config)
            full_plan = MetroOrchestrator(token_policy=policy).plan(args.request)
            selected, skipped = policy.select_steps(full_plan.steps)
            _dump(
                {
                    "policy": asdict(policy),
                    "selected_steps": [asdict(step) for step in selected],
                    "skipped_agents": list(skipped),
                    "mandatory_final_audit": full_plan.mandatory_final_audit,
                    "note": "Token counts are conservative estimates, not provider billing counters.",
                }
            )
        elif args.command == "library":
            library = DocumentLibrary.load(args.catalog) if args.catalog else DocumentLibrary.load_default()
            _dump([item.to_dict() for item in library.search(args.query, args.publisher)])
        elif args.command == "pdf-search":
            library = GovernedPdfLibrary.from_source_roots(
                args.sources, source_id=args.source_id
            )
            _dump([item.to_dict() for item in library.search(args.query)])
        elif args.command == "pdf-extract":
            if args.chunk <= 0:
                raise ValueError("chunk must be a positive one-based index")
            library = GovernedPdfLibrary.from_source_roots(
                args.sources, source_id=args.source_id
            )
            selected = None
            for index, chunk in enumerate(
                library.iter_chunks(args.record_id, chunk_size=args.chunk_size), start=1
            ):
                if index == args.chunk:
                    selected = chunk
                    break
            if selected is None:
                raise ValueError(f"chunk {args.chunk} is outside the document")
            _dump(selected.to_dict())
        elif args.command in {
            "budget",
            "compare",
            "paired",
            "separate",
            "uncertainty-study",
        }:
            payload = _load_json(args.input)
            request = CalculationRequest("cli", args.command, payload)
            if (
                args.command == "uncertainty-study"
                and args.note_out is not None
                and Path(args.note_out).exists()
            ):
                raise FileExistsError(f"note output already exists: {args.note_out}")
            record = engine.execute(request, execution_origin="cli:structured_input")
            _write_trace(args.trace_out, record)
            if args.command == "uncertainty-study" and record.status == "ok":
                _write_new_text(
                    args.note_out,
                    str(record.result["latex_note"]),
                    label="note",
                )
            _dump(record.to_dict())
            if record.status != "ok":
                print(f"error: {record.error}", file=sys.stderr)
                return 2
        elif args.command == "uncertainty-verify":
            study = build_uncertainty_study(_load_json(args.input))
            checks = verify_with_external_oracles(study)
            _dump(
                {
                    "expected_combined_standard_uncertainty": (
                        study.budget.combined_standard_uncertainty
                    ),
                    "unit": study.budget.unit,
                    "oracles": [item.to_dict() for item in checks],
                }
            )
            if any(item.status == "mismatch" for item in checks):
                return 2
        elif args.command == "module-list":
            store = ModuleStore(args.root, reserved_ids=BUILTIN_OPERATIONS)
            governed = [record.to_dict() for record in store.list_records()]
            active_engine = DeterministicEngine.from_store(store)
            _dump(
                {
                    "available_modules": active_engine.list_modules(),
                    "governed_records": governed,
                }
            )
        elif args.command == "module-submit":
            store = ModuleStore(args.root, reserved_ids=BUILTIN_OPERATIONS)
            _dump(
                store.submit(
                    _load_json(args.manifest), created_by=args.created_by
                ).to_dict()
            )
        elif args.command == "module-test":
            store = ModuleStore(args.root, reserved_ids=BUILTIN_OPERATIONS)
            _dump(store.test(args.module_id, args.version).to_dict())
        elif args.command == "module-promote":
            store = ModuleStore(args.root, reserved_ids=BUILTIN_OPERATIONS)
            _dump(
                store.promote(
                    args.module_id,
                    args.version,
                    approved_by=args.approved_by,
                ).to_dict()
            )
        elif args.command == "module-deprecate":
            store = ModuleStore(args.root, reserved_ids=BUILTIN_OPERATIONS)
            _dump(
                store.deprecate(
                    args.module_id,
                    args.version,
                    approved_by=args.approved_by,
                    reason=args.reason,
                ).to_dict()
            )
        elif args.command == "module-rollback":
            store = ModuleStore(args.root, reserved_ids=BUILTIN_OPERATIONS)
            _dump(
                store.rollback(
                    args.module_id,
                    args.version,
                    approved_by=args.approved_by,
                ).to_dict()
            )
        elif args.command == "module-run":
            store = ModuleStore(args.root, reserved_ids=BUILTIN_OPERATIONS)
            active_engine = DeterministicEngine.from_store(store)
            request = CalculationRequest(
                "cli-module", args.module_id, _load_json(args.input)
            )
            record = active_engine.execute(
                request, execution_origin="cli:structured_input"
            )
            _write_trace(args.trace_out, record)
            _dump(record.to_dict())
            if record.status != "ok":
                print(f"error: {record.error}", file=sys.stderr)
                return 2
        elif args.command == "knowledge-list":
            store = KnowledgeStore(args.root)
            _dump([record.to_dict() for record in store.list_records()])
        elif args.command == "knowledge-search":
            store = KnowledgeStore(args.root)
            if args.mode == "hybrid":
                if args.include_candidates:
                    raise ValueError(
                        "hybrid search indexes validated knowledge only; use --mode lexical "
                        "to inspect candidates"
                    )
                hits = HybridRagRetriever(store).search(
                    args.query,
                    limit=args.limit,
                )
            else:
                hits = store.search(
                    args.query,
                    include_candidates=args.include_candidates,
                    limit=args.limit,
                )
            _dump(
                [
                    hit.to_dict()
                    for hit in hits
                ]
            )
        elif args.command == "knowledge-promote":
            store = KnowledgeStore(args.root)
            _dump(
                store.promote(
                    args.knowledge_id,
                    approved_by=args.approved_by,
                    reason=args.reason,
                ).to_dict()
            )
        elif args.command == "knowledge-supersede":
            store = KnowledgeStore(args.root)
            _dump(
                store.supersede(
                    args.knowledge_id,
                    approved_by=args.approved_by,
                    reason=args.reason,
                ).to_dict()
            )
        elif args.command == "study-list":
            store = StudyStore(args.root)
            _dump([asdict(item) for item in store.list_studies()])
        elif args.command == "study-show":
            store = StudyStore(args.root)
            _dump(store.load(args.study_id, args.revision).to_dict())
        elif args.command == "study-export":
            store = StudyStore(args.root)
            snapshot = store.load(args.study_id, args.revision)
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                render_study_report(
                    snapshot,
                    args.kind,
                    organization=args.organization,
                    prepared_by=args.prepared_by,
                ),
                encoding="utf-8",
            )
            _dump(
                {
                    "study_id": snapshot.study_id,
                    "revision": snapshot.revision,
                    "kind": args.kind,
                    "output": str(output.resolve()),
                    "source_integrity_sha256": snapshot.integrity_sha256,
                }
            )
        return 0
    except (
        ArithmeticError,
        KeyError,
        TypeError,
        ValueError,
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def public_main(argv: list[str] | None = None) -> int:
    return main(argv, prog="metrology-lab-ai")

