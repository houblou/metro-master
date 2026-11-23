"""Exemple de branchement de PDF-EXTRACTOR sur la bibliothèque gouvernée."""

from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401

from metro_master.orchestrator import MetroOrchestrator
from metro_master.pdf_library import GovernedPdfLibrary


class PdfDemoBackend:
    """Démonstrateur : remplacer le corps par un appel LLM autorisé."""

    def complete(
        self,
        *,
        agent: str,
        system_prompt: str,
        user_request: str,
        shared_context: str,
    ) -> str:
        context = json.loads(shared_context)
        if agent == "PDF-EXTRACTOR" and context["task_phase"] == "extract_chunk":
            chunk = context["document_chunk"]
            return (
                f"DÉMONSTRATION — lot {chunk['document_id']} "
                f"pages {chunk['start_page']}-{chunk['end_page']} reçu."
            )
        if agent == "PDF-EXTRACTOR":
            internal = [
                turn
                for turn in context["turns"]
                if turn["agent"] == "PDF-EXTRACTOR"
            ]
            return f"DÉMONSTRATION — synthèse de {len(internal)} lots paginés."
        return f"DÉMONSTRATION — {agent} a reçu le rapport documentaire."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("record_id")
    parser.add_argument("--sources", default="library/source-roots.json")
    args = parser.parse_args()
    library = GovernedPdfLibrary.from_source_roots(args.sources)
    result = MetroOrchestrator().execute_pdf_record(
        "Lire intégralement le PDF et produire un rapport métrologique paginé.",
        PdfDemoBackend(),
        library,
        args.record_id,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
