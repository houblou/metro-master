# MetrologyLab AI

**Assistant de métrologie open source en français pour l'incertitude de mesure, les comparaisons, l'étalonnage et les rapports auditables.**

MetrologyLab AI combine un skill Agent Skills, treize rôles spécialisés et un moteur Python déterministe. Il vise les laboratoires, ingénieurs et étudiants qui doivent conserver une séparation claire entre raisonnement assisté par IA, données sources et résultats numériques reproductibles.

## Capacités principales

- budgets d'incertitude avec corrélations et coefficients de sensibilité typés ;
- comparaison banc/référence et séparation explicite des effets partagés ;
- traçabilité des calculs, preuves par champ et audit final obligatoire ;
- méthodes alignées sur le vocabulaire JCGM/GUM et les besoins ISO/IEC 17025 ;
- statistiques d'ingénierie, RAG documentaire gouverné et gestion des tokens ;
- compatibilité ChatGPT, Codex, Claude Code et orchestrateurs Python.

## Installation

```bash
python -m pip install metrology-lab-ai
metrology-lab-ai --version
```

Pour installer le skill depuis GitHub :

```bash
npx skills add houblou/metrology-lab-ai --skill metrology-lab-ai
```

## Commencer

Consultez [l'architecture](architecture.md), [l'exécution structurée](structured-execution.md) et [la méthode de comparaison](comparison-method.md). Le code source, les issues et les releases sont disponibles sur [GitHub](https://github.com/houblou/metrology-lab-ai). Le paquet Python est publié sur [PyPI](https://pypi.org/project/metrology-lab-ai/).

!!! warning "Périmètre"
    MetrologyLab AI aide à construire et auditer une étude. Il ne remplace ni la validation d'un responsable métrologique, ni un certificat signé, ni une décision d'accréditation.
