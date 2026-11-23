"""Rapports traçables et projets non officiels issus d'une étude persistée."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .study_history import StudySnapshot


REPORT_KINDS = frozenset(
    {"technical-report", "draft-certificate", "accreditation-assessment"}
)


def _turns(snapshot: StudySnapshot) -> list[dict[str, Any]]:
    value = snapshot.orchestration.get("turns", [])
    return value if isinstance(value, list) else []


def _calculations(snapshot: StudySnapshot) -> list[tuple[str, dict[str, Any]]]:
    records = []
    for turn in _turns(snapshot):
        agent = str(turn.get("agent", "unknown"))
        calculations = turn.get("calculations", [])
        if isinstance(calculations, list):
            for record in calculations:
                if isinstance(record, dict):
                    records.append((agent, record))
    return records


def _research_sources(snapshot: StudySnapshot) -> list[dict[str, Any]]:
    sources = []
    seen = set()
    for turn in _turns(snapshot):
        records = turn.get("research_records", [])
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            for source in record.get("sources", []):
                if not isinstance(source, dict):
                    continue
                url = str(source.get("url", ""))
                if url and url not in seen:
                    seen.add(url)
                    sources.append(source)
    return sources


def _header(snapshot: StudySnapshot, title: str) -> list[str]:
    return [
        f"# {title}",
        "",
        f"- Étude : `{snapshot.study_id}`",
        f"- Révision : `{snapshot.revision}`",
        f"- Créée : `{snapshot.created_at}`",
        f"- Empreinte : `{snapshot.integrity_sha256}`",
        f"- Exporté : `{datetime.now(timezone.utc).isoformat()}`",
        "",
    ]


def render_technical_report(snapshot: StudySnapshot) -> str:
    lines = _header(snapshot, "Rapport technique MetrologyLab AI")
    lines.extend(["## Demande", "", snapshot.request, "", "## Exécutions", ""])
    calculations = _calculations(snapshot)
    if not calculations:
        lines.append("Aucun calcul déterministe enregistré.")
    for agent, record in calculations:
        request = record.get("request", {})
        lines.extend(
            [
                f"### {request.get('id', 'sans-id')} — {agent}",
                "",
                f"- Opération : `{request.get('operation', '')}`",
                f"- Statut : `{record.get('status', '')}`",
                f"- Provenance : `{record.get('provenance_status', 'not_checked')}`",
                f"- Résultat : `{record.get('result')}`",
                f"- Erreur : `{record.get('error') or ''}`",
                "",
            ]
        )
    verification = snapshot.orchestration.get("conclusion_verification") or {}
    lines.extend(
        [
            "## Vérification de la conclusion",
            "",
            f"- Statut numérique : `{verification.get('status', 'absent')}`",
            "- Portée : vérification des affirmations numériques structurées uniquement.",
            "- Revue sémantique et métrologique humaine toujours requise.",
            "",
            "## Sources Web enregistrées",
            "",
        ]
    )
    sources = _research_sources(snapshot)
    if not sources:
        lines.append("Aucune source Web enregistrée.")
    for source in sources:
        lines.append(
            f"- {source.get('publisher') or 'Organisme non indiqué'}, "
            f"*{source.get('title', '')}*, {source.get('url', '')}, "
            f"consulté le {source.get('retrieved_at', 'date inconnue')}."
        )
    lines.extend(
        [
            "",
            "## Limites",
            "",
            "Ce rapport documente une exécution logicielle. Il ne remplace ni la revue "
            "du responsable métrologique, ni les procédures qualité du laboratoire.",
            "",
        ]
    )
    return "\n".join(lines)


def render_draft_certificate(
    snapshot: StudySnapshot,
    *,
    organization: str = "[organisme à renseigner]",
    prepared_by: str = "[préparateur à renseigner]",
) -> str:
    lines = _header(
        snapshot,
        "PROJET NON OFFICIEL — dossier préparatoire de certificat",
    )
    lines.extend(
        [
            "> **NE CONSTITUE PAS UN CERTIFICAT D'ÉTALONNAGE.** Ce projet ne devient "
            "officiel qu'après contrôle selon le système qualité, attribution d'un numéro, "
            "validation du domaine et signature par une personne habilitée.",
            "",
            f"- Organisme pressenti : {organization}",
            f"- Préparé par : {prepared_by}",
            "- Numéro officiel : [non attribué]",
            "- Signataire habilité : [validation requise]",
            "- Portée d'accréditation : [à vérifier par l'organisme habilité]",
            "",
            "## Résultats candidats",
            "",
        ]
    )
    calculations = _calculations(snapshot)
    if not calculations:
        lines.append("Aucun résultat publiable n'est disponible.")
    for agent, record in calculations:
        request = record.get("request", {})
        lines.extend(
            [
                f"### {request.get('id', 'sans-id')}",
                "",
                f"- Agent demandeur : `{agent}`",
                f"- Statut moteur : `{record.get('status', '')}`",
                f"- Statut provenance : `{record.get('provenance_status', 'not_checked')}`",
                f"- Résultat brut : `{record.get('result')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Contrôles obligatoires avant émission",
            "",
            "- [ ] identification de l'objet et du client ;",
            "- [ ] méthode, conditions et traçabilité métrologique ;",
            "- [ ] résultats, unités, incertitudes et règle d'arrondi ;",
            "- [ ] conformité au modèle documentaire du laboratoire ;",
            "- [ ] vérification de la portée d'accréditation ;",
            "- [ ] revue indépendante et signature habilitée ;",
            "- [ ] contrôle de l'intégrité de l'étude source.",
            "",
        ]
    )
    return "\n".join(lines)


def render_accreditation_assessment(snapshot: StudySnapshot) -> str:
    verification = snapshot.orchestration.get("conclusion_verification") or {}
    calculations = _calculations(snapshot)
    rejected = [
        record
        for _, record in calculations
        if record.get("status") != "ok"
    ]
    readiness = (
        "PRÊT POUR REVUE HUMAINE"
        if calculations
        and verification.get("status") == "verified"
        and not rejected
        else "PREUVES INSUFFISANTES"
    )
    lines = _header(
        snapshot,
        "Aide à la décision — préparation d'une revue d'accréditation",
    )
    lines.extend(
        [
            "> **CE DOCUMENT N'ACCORDE, NE RETIRE ET NE MODIFIE AUCUNE ACCRÉDITATION.** "
            "Seul l'organisme d'accréditation compétent peut prendre cette décision.",
            "",
            f"- État de préparation : **{readiness}**",
            f"- Vérification numérique de conclusion : `{verification.get('status', 'absent')}`",
            f"- Calculs rejetés : `{len(rejected)}`",
            f"- Sources Web enregistrées : `{len(_research_sources(snapshot))}`",
            "",
            "## Matrice de revue minimale",
            "",
            "| Axe | Preuve logicielle | Décision humaine requise |",
            "|---|---|---|",
            f"| Intégrité du dossier | SHA-256 `{snapshot.integrity_sha256}` | Vérifier la chaîne et les droits d'accès |",
            f"| Résultats numériques | {len(calculations)} enregistrement(s) | Confirmer modèle, domaine et unités |",
            f"| Conclusion | `{verification.get('status', 'absent')}` | Examiner le sens et l'applicabilité |",
            f"| Sources | {len(_research_sources(snapshot))} source(s) | Vérifier textes applicables et éditions |",
            "| Portée d'accréditation | Non déterminée par le logiciel | Décision réservée à l'organisme compétent |",
            "",
        ]
    )
    return "\n".join(lines)


def render_study_report(
    snapshot: StudySnapshot,
    kind: str,
    *,
    organization: str = "[organisme à renseigner]",
    prepared_by: str = "[préparateur à renseigner]",
) -> str:
    if kind not in REPORT_KINDS:
        raise ValueError(f"unknown report kind: {kind}")
    if kind == "technical-report":
        return render_technical_report(snapshot)
    if kind == "draft-certificate":
        return render_draft_certificate(
            snapshot,
            organization=organization,
            prepared_by=prepared_by,
        )
    return render_accreditation_assessment(snapshot)
