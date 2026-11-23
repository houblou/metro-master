"""Permet les tests du layout ``src`` sans installation préalable.

Utiliser ``python -m unittest discover -s tests -t .`` pour charger ce paquet.
"""

from pathlib import Path
import sys


SOURCE_ROOT = str(Path(__file__).resolve().parents[1] / "src")
if SOURCE_ROOT not in sys.path:
    sys.path.insert(0, SOURCE_ROOT)
