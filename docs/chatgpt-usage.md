# Utilisation dans ChatGPT

## Configuration recommandée

Pour chaque spécialiste, exécuter `metro-master prompt NOM`, puis copier la sortie complète dans les instructions du GPT correspondant. Ajouter uniquement les documents que vous êtes autorisé à utiliser. Dans la fiche documentaire de chaque fichier, conserver la référence, l'édition, la langue et l'empreinte.

Une alternative plus simple consiste à ne créer qu'un GPT `METRO-MASTER` et à lui fournir les prompts des spécialistes comme ressources. Ce mode simule les rôles dans une seule conversation ; il ne crée pas neuf processus indépendants.

## Workflow manuel multi-GPT

1. Demander au coordinateur un dossier de cadrage et un ordre de consultation.
2. Transmettre ce dossier au premier spécialiste choisi.
3. Ajouter chaque réponse au dossier en indiquant l'agent, la date et les sources réellement consultées.
4. Faire exécuter les calculs par Python et joindre le JSON de sortie.
5. Terminer par `METRO-AUDIT`, sans lui demander de réécrire silencieusement les résultats.

Les GPT personnalisés ne s'échangent pas de messages de manière automatique. Une automatisation réelle exige un orchestrateur (le module Python livré ou une autre couche explicitement configurée).

## Règle documentaire

Un lien ou une notice de catalogue prouve l'existence et les métadonnées d'un document, pas son contenu détaillé. Si le texte n'est pas joint, demander à l'agent de répondre : « métadonnées seulement ; clause à vérifier sur l'exemplaire autorisé ». Pour un extrait, limiter l'analyse à l'extrait et ne pas extrapoler au document complet.

## Format de passage de relais

```text
ID d'étude :
Version :
Demande et décision attendue :
Mesurande, unité, domaine :
Résultat du banc / référence :
Composantes banc / référence / partagées / transfert / protocole :
Corrélations et justification :
Données brutes et conditions :
Documents réellement disponibles :
Hypothèses :
Points ouverts :
Sortie JSON du moteur :
```

