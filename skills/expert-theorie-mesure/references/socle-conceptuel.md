# Socle conceptuel et contrat multi-agents

## Hiérarchie des sources

Privilégier, dans cet ordre :

1. le référentiel explicitement applicable au cas étudié ;
2. les publications officielles du JCGM et du BIPM, notamment le VIM et la famille GUM ;
3. les normes et exigences sectorielles applicables ;
4. les procédures et certificats du laboratoire ;
5. les articles pédagogiques ou techniques dont les droits autorisent l'usage prévu.

En cas de divergence, ne pas fusionner les formulations. Identifier la version, la date, le domaine d'application et la source qui gouverne le cas.

## Noyau de raisonnement

Un mesurage part d'un besoin d'information et d'une utilisation prévue. Le résultat n'est pas seulement une indication instrumentale. Il dépend de la définition du mesurande, d'une procédure, d'un système de mesure, de conditions de mesure et d'un modèle reliant une grandeur de sortie aux grandeurs d'entrée.

Le modèle peut être implicite, $h(Y,X_1,\ldots,X_n)=0$, ou explicite, $Y=f(X_1,\ldots,X_n)$. Les grandeurs d'entrée peuvent inclure des indications, des corrections et des grandeurs d'influence. Une entrée peut elle-même être la sortie d'un autre système de mesure.

Le résultat doit être accompagné des informations pertinentes pour être interprété. Dans le cas courant, cela inclut une valeur mesurée et une incertitude de mesure. La traçabilité relie le résultat à une référence au moyen d'une chaîne documentée d'étalonnages, chacun contribuant à l'incertitude.

Pour l'incertitude :

- recenser les sources à partir du modèle et de la procédure ;
- évaluer chaque composante par une méthode de type A ou B selon l'information disponible ;
- convertir l'information en incertitudes-types en justifiant les lois et diviseurs ;
- intégrer les covariances lorsque des entrées sont corrélées ;
- propager les incertitudes avec une méthode compatible avec le modèle ;
- employer Monte-Carlo lorsque la linéarisation est insuffisante ou que la distribution de sortie rend l'approximation classique inadaptée ;
- associer tout intervalle ou facteur d'élargissement à une probabilité de couverture et à des hypothèses explicites ;
- traiter l'évaluation de conformité comme une décision avec une règle et un risque, pas comme une simple comparaison naïve à une limite.

## Références officielles de départ

- JCGM 200:2012, *Vocabulaire international de métrologie — Concepts fondamentaux et généraux et termes associés (VIM)* : https://www.bipm.org/documents/20126/2071204/JCGM_200_2012.pdf
- JCGM 100:2008, *Évaluation des données de mesure — Guide pour l'expression de l'incertitude de mesure*.
- JCGM 100:2008/Amd.1:2026, amendement sur la non-linéarité des modèles de mesure.
- JCGM 101:2008, propagation des distributions par une méthode de Monte-Carlo.
- JCGM 106:2012, rôle de l'incertitude dans l'évaluation de conformité.
- JCGM GUM-6:2020, développement et utilisation des modèles de mesure.
- Page officielle des guides JCGM : https://www.bipm.org/en/publications/guides

Vérifier la version en vigueur et le référentiel contractuellement applicable avant de conclure.

## Documents privés ou à accès restreint

Les documents couverts par une licence personnelle restent hors du dépôt public, du catalogue distribué, des manifestes, des prompts et des compétences installables. Ne pas publier leur titre, référence, URL privée, empreinte, extrait ou résumé interne. Leur utilisation locale éventuelle doit rester dans l'environnement autorisé et ne doit produire dans le dépôt qu'un résultat original dont la diffusion est permise.

## Contrat avec les autres agents

| Agent | Entrée | Sortie | Limite |
|---|---|---|---|
| Chercheur documentaire | question, référence ou lacune | sources vérifiées et statut documentaire | ne décide pas du modèle de mesure |
| Extracteur PDF | document identifié | extraction paginée, formules et exigences | n'interprète pas au-delà du texte |
| Expert en théorie de la mesure | besoin, données et sources | mesurande, modèle, incertitude, hypothèses et avis conceptuel | n'invente pas les données manquantes |
| Expert de domaine | modèle conceptuel et procédé réel | effets physiques, paramètres et limites du procédé | ne remplace pas le référentiel métrologique |
| Implémenteur | modèle validé et règles de calcul | code, tests et traçabilité des calculs | ne modifie pas le modèle sans signalement |
| Curateur | rapports validés | intégration documentaire et liens | ne réinterprète pas les conclusions |

Chaque passage de relais doit préserver la provenance, les unités, les hypothèses et le statut de validation.

