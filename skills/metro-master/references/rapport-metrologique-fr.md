# Conduite et reprise d'un rapport métrologique — workflow français

## Statut et provenance

Ce workflow a été rédigé indépendamment pour METRO-MASTER. Il reprend l'idée générale d'une orchestration par phases et d'une reprise consciente de l'état d'un dossier. Le dépôt public `jeandead/metrology_assistant`, consulté au commit `8dd0d41843514f2740628abaae4f75d2dedcd72d` le 22 novembre 2026, ne présentait pas de licence explicite détectée. Aucun texte, code, gabarit, structure de fichiers ou instruction détaillée n'en est copié.

Le workflow ci-dessous est spécifique à l'architecture, aux garde-fous et aux formats de METRO-MASTER.

## Quand charger cette référence

La charger lorsque l'utilisateur demande :

- de créer un rapport, mémoire technique ou dossier d'étude ;
- de reprendre un rapport existant ;
- de poursuivre « là où on s'est arrêté » ;
- d'auditer la cohérence entre protocole, données, calculs et conclusion ;
- de produire un livrable Markdown, LaTeX, Word ou PDF à partir d'une étude.

Ne pas la charger pour une explication métrologique courte ou un calcul isolé.

## Principe de reprise consciente de l'état

Avant de poser une question sur l'avancement :

1. inventorier les fichiers du dossier autorisé ;
2. repérer manifeste, données brutes, calculs, figures, sections et exports ;
3. lire uniquement les fichiers nécessaires pour identifier la dernière étape réellement démontrée ;
4. distinguer `absent`, `présent`, `complet`, `vérifié` et `approuvé` ;
5. proposer l'étape suivante avec les preuves observées.

Ne jamais considérer un fichier vide, un titre, un commentaire `TODO` ou un export ancien comme une étape validée. Si l'état est ambigu et que les branches conduisent à des travaux différents, demander une confirmation ciblée.

## Manifeste recommandé

Conserver un fichier d'état versionnable, par exemple `report-state.json` :

```json
{
  "study_id": "",
  "report_title": "",
  "current_phase": "evidence_inventory",
  "phases": {
    "scope_protocol": "complete",
    "evidence_inventory": "in_progress",
    "measurement_model": "pending",
    "data_validation": "pending",
    "deterministic_analysis": "pending",
    "methods_results": "pending",
    "discussion_conclusion": "pending",
    "executive_sections": "pending",
    "final_audit": "pending"
  },
  "inputs": [],
  "calculations": [],
  "open_questions": [],
  "approvals": [],
  "last_verified_at": ""
}
```

Ce manifeste facilite la reprise mais ne remplace pas l'inspection des artefacts. Ne pas modifier un état vers `complete` sans critère de sortie satisfait.

## Phases du rapport

### 1. Périmètre et protocole

Définir décision, mesurande, domaine, équipement, référence, conditions, séquence, sécurité, critères d'acceptation et données à enregistrer.

Critère de sortie : protocole exécutable, grandeurs et responsabilités identifiées, points bloquants visibles.

### 2. Inventaire des preuves

Recenser données brutes, journaux, certificats, fichiers d'instrument, photos autorisées, manuels, normes, versions logicielles et empreintes. Classer les documents par état d'accès.

Critère de sortie : chaque résultat prévu possède une source attendue ; les absences sont déclarées.

### 3. Mesurande et modèle

Formaliser `Y=f(X)` ou `h(Y,X)=0`, définir les symboles, influences, corrections, corrélations, domaine et identifiabilité. Appeler THEORIA, PHYS-METRO ou METRO-COMPARE selon le cas.

Critère de sortie : modèle vérifiable et hypothèses séparées des faits.

### 4. Validation des données

Conserver les données brutes, unités, ordre et conditions. Contrôler valeurs manquantes, doublons, sentinelles, cohérence, dérive, résolution et exclusions. Appliquer l'EDA ou la caractérisation NIST seulement si utile.

Critère de sortie : jeu d'analyse traçable vers les données brutes, exclusions motivées.

### 5. Analyse déterministe

Construire les entrées JSON prouvées et exécuter les calculs disponibles. Conserver résultats `ok` et `rejected`. Produire tableaux et figures à partir des mêmes données versionnées.

Critère de sortie : tous les nombres importants du rapport pointent vers un calcul ou une source identifiée.

### 6. Méthode, résultats et discussion

Rédiger la méthode réellement exécutée, pas le protocole idéal. Présenter résultats avant interprétation. Comparer observations, modèle, incertitude, critères et littérature autorisée. Expliquer les écarts sans fabriquer de causalité.

Critère de sortie : cohérence entre protocole, données, calculs, figures et texte.

### 7. Conclusion et actions

Répondre à la décision initiale, limiter le domaine, distinguer démontré/non démontré et proposer l'action suivante la plus utile. Utiliser les verdicts METRO-MASTER.

Critère de sortie : chaque conclusion chiffrée est vérifiable et aucune réserve critique n'est masquée.

### 8. Sections exécutives

Écrire ou réviser introduction, résumé, titre, mots-clés et liste des symboles après stabilisation du corps. Cela évite de promettre une méthode ou un résultat qui a changé pendant l'analyse.

Critère de sortie : résumé et introduction concordent avec le rapport final.

### 9. Audit transversal et export

Faire contrôler par METRO-AUDIT : science, calculs, expérience, documents, cohérence des renvois, versions, figures, unités, bibliographie et statut officiel. Compiler ou exporter ensuite sans corriger silencieusement une erreur scientifique.

Critère de sortie : audit enregistré, défauts bloquants levés ou explicitement acceptés par l'autorité compétente.

## Organisation de dossier recommandée

Adapter aux fichiers existants ; ne pas réorganiser sans besoin.

```text
study/
  report-state.json
  sources/
  raw-data/
  processed-data/
  calculations/
  figures/
  sections/
  audit/
  exports/
```

Préserver les noms et chemins existants lorsqu'ils sont déjà utilisés par des scripts ou des liens. Une migration de structure doit être explicite et vérifiée.

## Formats de sortie

- Markdown : source lisible et versionnable ;
- LaTeX : publication technique et équations, si la chaîne de compilation est disponible ;
- Word : relecture institutionnelle, si demandée ;
- PDF : artefact de diffusion, jamais source unique de vérité ;
- JSON/CSV : calculs, données et état machine-readable.

Le format n'accorde aucune autorité supplémentaire. Un projet de certificat reste non officiel jusqu'à signature habilitée.

## Audit de cohérence

Contrôler au minimum :

- même mesurande, unité, domaine et convention partout ;
- nombres identiques entre calculs, tableaux, figures, résumé et conclusion ;
- figures issues des bonnes versions de données ;
- exclusions et corrections décrites ;
- hypothèses et corrélations visibles ;
- sources réellement consultées et statut d'accès ;
- aucune exigence attribuée à une notice seule ;
- résultats rejetés non présentés comme valides ;
- limites et conditions reprises dans le résumé.

## Règles de rédaction

- Écrire ce qui a été fait et observé, pas une procédure fictive.
- Séparer résultat, interprétation et hypothèse causale.
- Préférer un tableau ou une figure quand ils réduisent réellement l'ambiguïté.
- Définir chaque symbole et conserver les unités.
- Ne pas remplir une section par du texte générique pour simuler l'avancement.
- Rendre visibles les décisions humaines et les éléments encore à approuver.

## Livrable de reprise

Lors d'une reprise, rendre d'abord :

1. état observé du dossier ;
2. dernière phase démontrée ;
3. incohérences ou artefacts périmés ;
4. informations manquantes ;
5. prochaine action proposée ;
6. fichiers qui seront modifiés si l'utilisateur poursuit.
