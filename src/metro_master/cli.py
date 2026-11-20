"""Interface en ligne de commande de METRO-MASTER."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

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


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _dump(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="metro-master", description="Métrologie multi-agents et calculs vérifiables"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("agents", help="lister les agents")

    prompt = sub.add_parser("prompt", help="composer le prompt complet d'un agent")
    prompt.add_argument("agent")

    route = sub.add_parser("route", help="afficher le plan d'orchestration")
    route.add_argument("request")

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

    compare = sub.add_parser("compare", help="calculer un écart corrélé JSON")
    compare.add_argument("input")

    paired = sub.add_parser("paired", help="analyser des lectures appariées JSON")
    paired.add_argument("input")

    separate = sub.add_parser(
        "separate", help="séparer conditionnellement l'incertitude du banc"
    )
    separate.add_argument("input")

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


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    engine = DeterministicEngine()
    try:
        if args.command == "agents":
            _dump([{"name": item.name, "description": item.description} for item in list_agents()])
        elif args.command == "prompt":
            print(compose_prompt(args.agent))
        elif args.command == "route":
            _dump(MetroOrchestrator().plan(args.request).to_dict())
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
        elif args.command in {"budget", "compare", "paired", "separate"}:
            payload = _load_json(args.input)
            request = CalculationRequest("cli", args.command, payload)
            _dump(engine.calculate(request))
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
            _dump(active_engine.calculate(request))
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

