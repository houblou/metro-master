# ADR-0004 — Auto-extensibilité gouvernée par modules déclaratifs

**Statut :** accepté — 2026-11-05

**Décideurs :** responsable METRO-MASTER et approbateur humain nommé lors de la promotion

## Contexte

METRO-MASTER doit pouvoir acquérir de nouvelles capacités de calcul sans modifier silencieusement son noyau. Les modules peuvent être proposés par un agent, mais une sortie LLM n'est pas une source de confiance et ne doit jamais obtenir directement l'autorité d'exécuter du code arbitraire.

Le mécanisme doit préserver : reproductibilité, unités, résultats de référence, historique des versions, approbation humaine, retour arrière et séparation LLM/calcul déterministe.

## Options considérées

### A — Plugins Python chargés dans le processus

| Dimension | Évaluation |
|---|---|
| Complexité | Faible à moyenne |
| Puissance scientifique | Très élevée |
| Isolation | Très faible |
| Validation | Difficile : les tests ne prouvent pas l'absence d'effets de bord |
| Maintenance | Risque fort de dépendances et d'interfaces divergentes |

**Avantages :** liberté algorithmique, intégration Python immédiate.

**Inconvénients :** exécution de code arbitraire, accès aux fichiers et au réseau, corruption possible du processus, dépendances non maîtrisées. Une auto-promotion sûre est impossible sans sandbox supplémentaire.

### B — Workers Python isolés

| Dimension | Évaluation |
|---|---|
| Complexité | Élevée |
| Puissance scientifique | Très élevée |
| Isolation | Élevée si la sandbox est correctement configurée |
| Validation | Tests + quotas + politique de capacités |
| Maintenance | Infrastructure, IPC, observabilité et signatures |

**Avantages :** algorithmes avancés possibles avec confinement.

**Inconvénients :** coût architectural important, sécurité dépendante du système d'exploitation, gestion des environnements et dépendances.

### C — Langage déclaratif de formules

| Dimension | Évaluation |
|---|---|
| Complexité | Moyenne |
| Puissance scientifique | Moyenne |
| Isolation | Élevée : aucun `eval`, import, attribut ou appel arbitraire |
| Validation | Schéma strict + unités + cas de référence |
| Maintenance | Manifeste JSON portable et versionné |

**Avantages :** sûr, déterministe, testable, auditable, facile à promouvoir et à annuler.

**Inconvénients :** ne couvre pas directement régressions complexes, Monte-Carlo, optimisation ou traitements itératifs.

### D — Architecture hybride progressive

Modules déclaratifs dans le cœur sûr ; futurs modules Python uniquement dans des workers isolés et signés.

| Dimension | Évaluation |
|---|---|
| Complexité initiale | Moyenne |
| Évolutivité | Élevée |
| Sécurité initiale | Élevée |
| Couverture scientifique future | Très élevée |
| Coût | Progressif |

## Décision

Adopter l'option D avec une première implementation limitée aux modules déclaratifs :

1. un manifeste strict décrit identifiant, version, entrées avec unités, expression, sortie, références et cas de validation ;
2. l'expression est interprétée par un AST autorisé, jamais par `eval` ;
3. un module suit le cycle `candidate → validated → deprecated` ;
4. la promotion exige tous les cas de référence réussis et le nom d'un approbateur humain ;
5. les versions validées restent immuables et un index séparé désigne la version active ;
6. le retour arrière sélectionne une version validée antérieure sans réécrire son contenu ;
7. les opérations natives existantes restent enregistrées comme modules intégrés ;
8. les futurs modules Python devront faire l'objet d'un ADR séparé sur l'isolation.

## Conséquences

- METRO-MASTER peut grandir sans réécrire son noyau ni exécuter du Python généré.
- Un agent peut proposer un manifeste candidat, mais ne peut pas se promouvoir lui-même.
- Les unités et cas de référence deviennent obligatoires pour les modules déclaratifs.
- Les calculs complexes restent à développer dans le noyau ou dans un futur worker isolé.
- Le registre de fichiers devient une donnée gouvernée à sauvegarder et auditer.

## Actions

1. Créer `ModuleRegistry`, l'évaluateur sûr et le stockage versionné.
2. Enregistrer `budget`, `compare`, `paired` et `separate` comme modules natifs.
3. Ajouter les commandes de soumission, test, promotion, dépréciation, exécution et retour arrière.
4. Ajouter un manifeste d'exemple et des tests adversariaux.
5. Revoir ultérieurement le worker Python isolé pour Monte-Carlo et régressions avancées.
