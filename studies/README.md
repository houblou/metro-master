# Historique des études

`studies/registry/` reçoit les études persistées par `StudyStore`.

Chaque sous-dossier correspond à un `study_id`. Les fichiers `revision-000001.json`, `revision-000002.json`, etc. ne sont jamais remplacés. `previous_sha256` relie une révision à la précédente et `integrity_sha256` protège son contenu.

Le registre local est prévu pour un usage mono-processus. Un déploiement partagé doit ajouter verrouillage, contrôle d'accès, sauvegarde et identité forte.
