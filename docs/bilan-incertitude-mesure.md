---
title: Bilan d'incertitude de mesure — méthode GUM et calcul Python
description: Guide pratique pour construire un bilan d'incertitude traçable avec modèle de mesure, corrélations, coefficients de sensibilité et contrôles GUM.
---

# Bilan d'incertitude de mesure

Un bilan d'incertitude relie une grandeur mesurée, un modèle, des données et une décision. MetrologyLab AI aide à construire ce lien de façon explicite : chaque valeur doit avoir une provenance, chaque hypothèse doit être déclarée et chaque résultat numérique doit pouvoir être recalculé.

Cette page décrit les capacités actuelles du moteur. Elle ne remplace pas l'analyse du domaine, la validation expérimentale ni l'interprétation des documents applicables.

## 1. Définir le mesurande

La première étape consiste à écrire précisément ce qui doit être mesuré et dans quelles conditions. Une indication d'instrument, une valeur corrigée, une moyenne de série et une propriété d'un processus ne sont pas nécessairement le même mesurande.

Le dossier doit au minimum préciser :

- la grandeur et son unité ;
- l'objet, le domaine et les conditions de mesure ;
- le résultat attendu et la décision associée ;
- les corrections appliquées ou volontairement non appliquées ;
- les limites d'usage du résultat.

## 2. Écrire le modèle de mesure

Pour un modèle explicite, le mesurande est représenté par :

\[
Y=f(X_1, X_2, \ldots, X_n)
\]

Les entrées peuvent représenter une indication, un étalon, une correction, une dérive, un effet de température, une résolution ou un terme de répétabilité. Le modèle doit éviter les doubles comptages : un même effet ne doit pas apparaître à la fois dans une dispersion expérimentale et dans une correction indépendante sans justification.

MetrologyLab AI utilise actuellement une propagation linéaire. Les coefficients de sensibilité peuvent être fournis avec leurs unités afin de contrôler la cohérence dimensionnelle du résultat.

## 3. Évaluer les incertitudes-types

Chaque composante est décrite par une incertitude-type. La méthode d'évaluation de type A ou B indique comment l'information a été obtenue ; elle ne détermine pas à elle seule la loi de probabilité ni le caractère aléatoire ou systématique de l'effet.

Les informations à conserver comprennent notamment :

- la valeur et l'unité d'origine ;
- la source documentaire ou expérimentale ;
- la loi retenue et sa justification ;
- le diviseur utilisé pour obtenir l'incertitude-type ;
- les degrés de liberté lorsqu'ils sont connus ;
- le coefficient de sensibilité ;
- les relations avec les autres composantes.

## 4. Traiter les corrélations

Pour une propagation linéaire, l'incertitude composée est calculée à partir des sensibilités et de la covariance :

\[
u_c^2(y)=\sum_i c_i^2u_i^2+2\sum_{i<j}c_ic_j\,\operatorname{cov}(X_i,X_j)
\]

avec :

\[
\operatorname{cov}(X_i,X_j)=r_{ij}u_i u_j
\]

La matrice de corrélation doit être symétrique, bornée et positive semi-définie. Mettre les corrélations à zéro faute d'information constitue une hypothèse qui doit être enregistrée, pas un fait automatiquement admis.

## 5. Choisir le facteur de couverture

L'incertitude élargie s'écrit généralement :

\[
U=k\,u_c(y)
\]

Le facteur de couverture doit être relié à une probabilité de couverture, une loi et des degrés de liberté pertinents. Le moteur sait appliquer Welch–Satterthwaite lorsque les composantes à degrés de liberté finis restent indépendantes et que l'approximation est justifiée.

Si les entrées sont corrélées ou si le modèle sort du domaine de validité de l'approximation, le logiciel ne fabrique pas un degré de liberté effectif. Ce point fait partie des axes prioritaires de la future architecture mathématique.

## 6. Exécuter et tracer le calcul

Un budget peut être fourni sous forme JSON puis exécuté avec :

```bash
metrology-lab-ai budget examples/budget_correlated.json --trace-out traces/budget.json
```

Le résultat contient les contributions individuelles, les termes de covariance, l'incertitude composée, l'incertitude élargie et une trace canonique. Une entrée incohérente produit un enregistrement `rejected` plutôt qu'un nombre silencieusement corrigé.

## 7. Vérifier le bilan

Avant validation, contrôler au minimum :

1. l'adéquation entre mesurande, modèle et décision ;
2. la couverture des effets significatifs ;
3. l'absence de double comptage ;
4. la cohérence des unités et des sensibilités ;
5. la justification des corrélations ;
6. la stabilité des données de type A ;
7. le domaine de validité de la linéarisation ;
8. le choix du facteur de couverture ;
9. la reproductibilité du calcul ;
10. la traçabilité de la conclusion vers les résultats.

## Limites actuelles

Le noyau standard ne couvre pas encore Monte-Carlo, les modèles implicites généraux, les régressions complètes avec covariance des paramètres, les distributions multivariées non gaussiennes ni une détermination générale des degrés de liberté effectifs en présence de corrélations.

Ces limites sont déclarées afin qu'une étude complexe soit orientée vers une méthode adaptée. La prochaine refonte mathématique devra ajouter ces capacités derrière des contrats de calcul stables, sans casser les traces, les études existantes ni la séparation entre agents et moteur déterministe.
