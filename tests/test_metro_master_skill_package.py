from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tomllib
import unittest

from metro_master import __version__


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "metro-master"


class MetroMasterSkillPackageTests(unittest.TestCase):
    def test_plugin_manifest_targets_v071_skill(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "metro-master")
        self.assertEqual(manifest["version"], "0.7.1")
        self.assertEqual(manifest["license"], "Apache-2.0")
        self.assertEqual(manifest["skills"], "./skills/")

    def test_declared_versions_are_consistent(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        expected = "0.7.1"
        self.assertEqual(project["project"]["version"], expected)
        self.assertEqual(manifest["version"], expected)
        self.assertEqual(__version__, expected)
        self.assertIn(f'version: "{expected}"', skill_text)

    def test_skill_is_portable_and_routes_to_progressive_references(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: metro-master", skill_text)
        self.assertIn('version: "0.7.1"', skill_text)
        self.assertIn("references/statistiques-nist-fr.md", skill_text)
        self.assertIn("references/rapport-metrologique-fr.md", skill_text)
        self.assertIn("references/runtime.md", skill_text)

        all_skill_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SKILL.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("C:\\Users\\julia", all_skill_text)

    def test_openai_metadata_invokes_the_installed_skill(self) -> None:
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name: \"METRO-MASTER\"", metadata)
        self.assertIn("$metro-master", metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_statistical_reference_retains_provenance_and_guards(self) -> None:
        reference = (SKILL / "references" / "statistiques-nist-fr.md").read_text(encoding="utf-8")
        self.assertIn("NIST/SEMATECH", reference)
        self.assertIn("domaine public", reference)
        self.assertIn("n'est approuvée", reference)
        for topic in ("Gauge R&R", "Stabilité avant capabilité", "régression", "CUSUM", "fiabilité"):
            self.assertIn(topic, reference)

    def test_report_reference_is_explicitly_independent(self) -> None:
        reference = (SKILL / "references" / "rapport-metrologique-fr.md").read_text(encoding="utf-8")
        self.assertIn("rédigé indépendamment", reference)
        self.assertIn("ne présentait pas de licence explicite", reference)
        self.assertIn("Aucun texte, code, gabarit", reference)
        self.assertIn("Principe de reprise consciente de l'état", reference)

    def test_portable_bridge_reaches_the_v071_engine(self) -> None:
        process = subprocess.run(
            [
                sys.executable,
                str(SKILL / "scripts" / "run_metro_master.py"),
                "--project-root",
                str(ROOT),
                "agents",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        agents = json.loads(process.stdout)
        self.assertEqual(len(agents), 13)
        names = {agent["name"] for agent in agents}
        self.assertIn("METRO-MASTER", names)
        self.assertIn("METRO-AUDIT", names)


if __name__ == "__main__":
    unittest.main()
