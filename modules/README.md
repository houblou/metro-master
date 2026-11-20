# Modules de calcul gouvernés

`examples/` contient des manifestes illustratifs non installés. `registry/` est créé par les commandes `module-*` et contient les définitions soumises, leur état de cycle de vie et l'index des versions actives.

Cycle obligatoire :

```text
manifest JSON → module-submit → module-test → module-promote
                                      ↑              ↓
                                 cas rejeté     version active
                                                     ↓
                                  module-deprecate / module-rollback
```

Une soumission crée seulement un candidat. La promotion exige au moins deux cas de référence réussis et `--approved-by`. Aucun manifeste ne peut importer ou exécuter du Python : les expressions passent par l'évaluateur AST autorisé.

Le contrat complet est publié dans `schema.json`. Après une promotion ou un rollback dans un processus déjà actif, appeler `MetroOrchestrator.refresh_modules()` ou `DeterministicEngine.load_store()`.

Le dossier `registry/` représente un état d'exécution local. Le sauvegarder avec le dossier d'étude lorsque les modules participent à un résultat publiable.
