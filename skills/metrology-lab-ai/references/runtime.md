# Intégration portable MetrologyLab AI

## Découverte du moteur

Utiliser dans cet ordre :

1. la commande `metro-master` si le paquet Python est installé ;
2. `python scripts/run_metro_master.py` depuis la compétence installée ;
3. définir `METRO_MASTER_PROJECT_ROOT` vers la racine du dépôt ;
4. passer `--project-root CHEMIN` au pont portable.

Le pont cherche une racine contenant `pyproject.toml` et `src/metro_master`. Il ne contient aucun chemin personnel et peut être copié avec la compétence.

## Vérification

À la racine du dépôt :

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m unittest discover -s tests -t . -q
```

Version de projet attendue : `0.9.2`. Le nom public est `metrology-lab-ai` / `metrology_lab_ai`; `metro-master` / `metro_master` restent des alias compatibles. Chaque livraison de maturation incrémente uniquement le correctif (`0.9.0` → `0.9.1` → `0.9.2`). Le passage à `1.0.0` exige une décision explicite de maturité ; une compétence améliorée ne l'annonce jamais automatiquement.

## Appels utiles

Depuis le dossier `skills/metrology-lab-ai` :

```powershell
py scripts\run_metro_master.py agents
py scripts\run_metro_master.py route "Caractériser un banc par comparaison"
py scripts\run_metro_master.py token-plan "Comparer trois méthodes" --mode standard
py scripts\run_metro_master.py prompt DATA-METRO --token-mode standard
py scripts\run_metro_master.py library --query "gauge R&R"
py scripts\run_metro_master.py pdf-search --query "JCGM 100"
py scripts\run_metro_master.py budget examples\budget_correlated.json
py scripts\run_metro_master.py study-list
```

Avec une racine explicite :

```powershell
py scripts\run_metro_master.py --project-root C:\chemin\metro-master agents
```

## Bibliothèque et droits

La bibliothèque gouvernée est déclarée par le dépôt dans `library/source-roots.json`. Les PDF locaux restent hors du paquet lorsqu'ils ne sont pas redistribuables. Vérifier empreinte, droits et état d'extraction avant d'attribuer une formule ou une exigence.

## Limites

- Une installation de la seule compétence apporte les instructions et le pont, pas les documents protégés.
- Les calculs nécessitent le paquet Python ou le dépôt source.
- La recherche Web nécessite un outil de navigation dans la conversation ou un `ResearchProvider` configuré.
- Une écriture dans les registres d'études, de connaissances ou de modules respecte toujours les autorisations de l'utilisateur.
