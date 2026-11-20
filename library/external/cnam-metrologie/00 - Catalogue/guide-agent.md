# Guide d'exploitation par les agents IA

## 1. Hiérarchie des sources

Un agent doit arbitrer les conflits dans cet ordre :

1. Exigence légale ou réglementaire applicable au cas étudié.
2. Norme contractuellement imposée et édition explicitement convenue.
3. Édition publiée et en vigueur de la norme ou du document d'accréditation.
4. Guides JCGM/BIPM, ILAC, EA, EURAMET et OIML pertinents.
5. Guides nationaux et documents des instituts nationaux de métrologie.
6. Articles évalués par les pairs et ouvrages de théorie de la mesure.
7. Documents internes validés.

Un projet de norme, une page de vulgarisation ou une réponse générée ne doit jamais être présenté comme une exigence normative.

## 2. Paquet documentaire minimal par tâche

### Vocabulaire et concepts

- JCGM 200:2012 (VIM), JCGM GUM-1:2023, Brochure sur le SI.
- Ajouter une ressource de théorie de la mesure seulement si la question dépasse les définitions opérationnelles.

### Budget d'incertitude

- JCGM 100:2008 et Amendement 1:2026.
- JCGM GUM-6:2020 pour construire le modèle.
- JCGM 101:2008 si le modèle est fortement non linéaire ou si l'approximation linéaire est douteuse.
- EA-4/02 M:2022 et ILAC P14:09/2020 pour l'étalonnage sous accréditation.

### Étalonnage et traçabilité

- ISO/IEC 17025:2017, ILAC P10:07/2020, ISO 10012:2026.
- Ajouter ISO 28037:2026 ou ISO/TS 28038:2018 pour une fonction d'étalonnage.
- Ajouter ILAC-G24/OIML D 10:2022 pour les intervalles de réétalonnage.

### Comparaison interlaboratoires ou essai d'aptitude

- ISO/IEC 17043:2023, ISO 13528:2022 + Amd 1:2026 et ILAC P9:01/2024.
- Ajouter EURAMET Guide No. 4 et CIPM MRA-G-11 pour une comparaison métrologique.
- Ajouter EA-4/21 INF:2026 pour une petite comparaison interlaboratoires.

### Déclaration de conformité

- JCGM 106:2012, ILAC G8:09/2019 et, en GPS dimensionnelle, ISO 14253-1:2017.
- Identifier la règle de décision avant de conclure ; documenter le risque consommateur/producteur et toute bande de garde.

## 3. Contrôles obligatoires avant réponse

Chaque réponse technique importante doit expliciter :

- le mesurande, l'unité et les conditions d'influence ;
- la chaîne de traçabilité et le rôle de chaque référence ;
- le modèle de mesure, les corrections et les hypothèses ;
- la distinction entre erreur, correction, incertitude, tolérance et erreur maximale tolérée ;
- le niveau de confiance ou la probabilité de couverture visée ;
- les corrélations éventuelles ;
- l'édition exacte des documents utilisés ;
- ce qui relève d'une exigence, d'une recommandation ou d'un choix méthodologique.

## 4. Règles anti-hallucination documentaire

- Ne pas inventer de clause, de page, d'annexe ou de citation.
- Si le texte intégral n'est pas disponible sous licence, limiter la réponse aux métadonnées et à l'abstract officiels, puis signaler la limite.
- Ne pas confondre les miroirs ISO/IEC Guide 98 avec les publications JCGM correspondantes ; préférer le JCGM libre pour l'analyse, tout en citant l'équivalence ISO pertinente.
- Ne pas présenter VIM4/ISO DGuide 99 comme publié : il reste un projet à la date de vérification.
- Ne pas présenter une norme retirée comme applicable sans justification contractuelle ou historique.
- Ne jamais déduire l'incertitude complète d'un banc de la seule différence entre deux bancs.

## 5. Format de provenance recommandé

Pour toute affirmation importante, l'agent conserve :

```text
Référence | édition/date | organisme | URL officielle | date de consultation | statut | licence/accès | extrait ou donnée utilisée
```

La date de consultation de cette version est `2026-11-05`. Toute utilisation ultérieure devrait recontrôler les lignes marquées `P3`, les pages dynamiques et les documents ISO signalés « à réviser ».

