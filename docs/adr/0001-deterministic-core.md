# ADR-0001 — Séparer raisonnement LLM et calcul déterministe

**Statut :** accepté — 2026-11-05

## Contexte

Les modèles de langage sont utiles pour cadrer un mesurande, repérer les hypothèses et produire une critique, mais ils peuvent varier, omettre une corrélation ou inventer une référence. Un budget d'incertitude doit être reproductible et auditable.

## Décision

Les agents produisent une proposition structurée. Les valeurs publiables sont calculées par des fonctions Python testées. L'orchestrateur transmet les sorties du moteur aux agents et l'auditeur compare toute valeur narrative à ces sorties.

## Conséquences

Les calculs sont stables et vérifiables. La traduction d'un modèle physique en entrées numériques reste une étape humaine/agent à valider. Les modèles non linéaires avancés demanderont un moteur supplémentaire plutôt qu'une improvisation du LLM.

