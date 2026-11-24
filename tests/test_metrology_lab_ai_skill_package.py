from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tomllib
import unittest

from metro_master import __version__


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "metrology-lab-ai"


class MetrologyLabAiSkillPackageTests(unittest.TestCase):
    def test_plugin_manifest_targets_v095_skill(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "metrology-lab-ai")
        self.assertEqual(manifest["version"], "0.9.5")
        self.assertEqual(manifest["license"], "Apache-2.0")
        self.assertEqual(manifest["skills"], "./skills/")

    def test_declared_versions_are_consistent(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        expected = "0.9.5"
        self.assertEqual(project["project"]["version"], expected)
        self.assertEqual(manifest["version"], expected)
        self.assertEqual(__version__, expected)
        self.assertIn(f'version: "{expected}"', skill_text)

    def test_skill_is_portable_and_routes_to_progressive_references(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: metrology-lab-ai", skill_text)
        self.assertIn('version: "0.9.5"', skill_text)
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
        self.assertIn("display_name: \"MetrologyLab AI\"", metadata)
        self.assertIn("$metrology-lab-ai", metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_statistical_reference_retains_provenance_and_guards(self) -> None:
        reference = (SKILL / "references" / "statistiques-nist-fr.md").read_text(encoding="utf-8")
        self.assertIn("NIST/SEMATECH", reference)
        self.assertIn("domaine public", reference)
        self.assertIn("n'est approuvée", reference)
        for topic in ("Gauge R&R", "Stabilité avant capabilité", "régression", "CUSUM", "fiabilité"):
            self.assertIn(topic, reference)

    def test_portable_bridge_reaches_the_v095_engine(self) -> None:
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

    def test_legacy_python_and_cli_names_remain_compatible(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["name"], "metrology-lab-ai")
        self.assertIn("metro-master", project["project"]["scripts"])
        self.assertIn("metrology-lab-ai", project["project"]["scripts"])
        self.assertTrue((ROOT / "src" / "metro_master").is_dir())
        self.assertTrue((ROOT / "src" / "metrology_lab_ai").is_dir())

    def test_public_python_alias_exports_the_engine(self) -> None:
        import metrology_lab_ai

        self.assertEqual(metrology_lab_ai.__version__, "0.9.5")
        self.assertTrue(hasattr(metrology_lab_ai, "DeterministicEngine"))

    def test_publication_and_pages_metadata_are_present(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(
            project["project"]["urls"]["Homepage"],
            "https://houblou.github.io/metrology-lab-ai/",
        )
        self.assertIn("scientific-computing", project["project"]["keywords"])
        self.assertTrue((ROOT / "mkdocs.yml").is_file())
        self.assertTrue((ROOT / "docs" / "robots.txt").is_file())
        self.assertTrue((ROOT / "docs" / "llms.txt").is_file())
        self.assertTrue((ROOT / "docs" / "indexnow-key.txt").is_file())
        self.assertTrue((ROOT / "docs" / "bilan-incertitude-mesure.md").is_file())
        self.assertTrue((ROOT / ".github" / "workflows" / "pages.yml").is_file())
        self.assertTrue((ROOT / ".github" / "workflows" / "publish-pypi.yml").is_file())
        pages_workflow = (
            ROOT / ".github" / "workflows" / "pages.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("https://api.indexnow.org/indexnow", pages_workflow)
        seo_template = (ROOT / "docs" / "overrides" / "main.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('property="og:title"', seo_template)
        self.assertIn('"@type": "FAQPage"', seo_template)


if __name__ == "__main__":
    unittest.main()
