---
title: Assistant métrologique Python — incertitudes GUM et ISO 17025
description: MetrologyLab AI aide à construire des bilans d'incertitude traçables, comparer des moyens de mesure et produire des rapports auditables en français.
---

# MetrologyLab AI

**Assistant métrologique open source en français pour les bilans d'incertitude, les comparaisons, l'étalonnage et les rapports auditables.**

MetrologyLab AI associe un skill Agent Skills, treize rôles spécialisés et un moteur Python déterministe. Il s'adresse aux laboratoires, ingénieurs, qualiticiens et étudiants qui veulent utiliser une IA sans lui déléguer silencieusement les calculs. Les données sources, les hypothèses, le raisonnement assisté et les résultats numériques restent séparés et traçables.

Le projet est disponible sous licence Apache-2.0. Le paquet Python s'installe depuis PyPI et le skill peut être utilisé avec ChatGPT, Codex, Claude Code ou un orchestrateur Python.

## Ce que le moteur calcule aujourd'hui

- propagation linéaire d'un budget d'incertitude avec unités ;
- coefficients de sensibilité typés et conversions dimensionnelles ;
- corrélations, covariances et contributions croisées ;
- incertitude-type composée et incertitude élargie ;
- degrés de liberté effectifs par Welch–Satterthwaite lorsque ses conditions sont satisfaites ;
- écart corrélé, erreur normalisée, score zêta et statistiques de paires ;
- séparation conditionnelle de la variance d'un banc lorsque l'identifiabilité est démontrée.

Chaque demande structurée produit un enregistrement de calcul, y compris lorsqu'elle est refusée. La trace conserve les entrées, les unités, les hypothèses, le module utilisé, la version, l'environnement et l'empreinte du résultat.

## Construire un bilan d'incertitude de mesure

Un bilan fiable ne commence pas par une formule. Il commence par le mesurande, la décision à prendre, le domaine d'emploi et le modèle de mesure. MetrologyLab AI guide ensuite l'identification des composantes, leur évaluation de type A ou B, les corrélations, les lois de probabilité, les coefficients de sensibilité et les preuves documentaires.

La page [Bilan d'incertitude de mesure](bilan-incertitude-mesure.md) présente la méthode, les équations prises en charge, les contrôles appliqués et les limites actuelles du moteur.

## Cas d'usage

### Caractérisation d'un banc

Comparer un banc à une référence en séparant explicitement l'incertitude du banc, celle de la référence, les effets partagés et l'incertitude propre au protocole. Le logiciel refuse une séparation non identifiable ou une covariance non justifiée.

### Préparation d'un étalonnage

Structurer le modèle de mesure, établir un budget, vérifier les unités et préparer un rapport technique. Le résultat reste un support de travail : il ne remplace ni la validation de méthode, ni la signature d'un laboratoire habilité.

### Analyse de données métrologiques

Appliquer des méthodes statistiques d'ingénierie, contrôler la stabilité, documenter les exclusions et conserver une chaîne de preuves entre les données et la conclusion.

### Dossier ISO/IEC 17025

Produire des éléments auditables pour une revue interne. MetrologyLab AI ne délivre aucune accréditation et ne transforme pas une référence documentaire en exigence si le texte applicable n'a pas réellement été fourni.

## Installation

```bash
python -m pip install metrology-lab-ai
metrology-lab-ai --version
```

Pour installer le skill depuis GitHub :

```bash
npx skills add houblou/metrology-lab-ai --skill metrology-lab-ai
```

Consultez ensuite [l'architecture](architecture.md), [l'exécution structurée](structured-execution.md), [la méthode de comparaison](comparison-method.md) et [la gestion des tokens](token-management.md). Le code source et les releases sont disponibles sur [GitHub](https://github.com/houblou/metrology-lab-ai), tandis que les distributions Python sont publiées sur [PyPI](https://pypi.org/project/metrology-lab-ai/).

## Questions fréquentes

### L'outil remplace-t-il un métrologue ?

Non. Il structure, calcule, vérifie et trace. La définition du mesurande, l'applicabilité des références, la validation de méthode et la décision finale restent sous responsabilité humaine.

### Peut-il traiter des composantes corrélées ?

Oui, la propagation linéaire accepte une matrice de corrélation justifiée et vérifie sa cohérence. En revanche, les degrés de liberté effectifs ne sont pas inventés lorsque les corrélations rendent l'approximation classique inapplicable.

### Peut-il traiter un modèle fortement non linéaire ?

Pas encore avec le noyau standard. Le projet signale cette limite et recommande une méthode adaptée, par exemple Monte-Carlo, au lieu de produire un résultat faussement précis.

!!! warning "Périmètre"
    MetrologyLab AI aide à construire et auditer une étude. Il ne remplace ni la validation d'un responsable métrologique, ni un certificat signé, ni une décision d'accréditation.
