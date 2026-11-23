# ADR-0002 — Exécution structurée et validation centralisée

**Statut :** accepté — 2026-11-05

## Contexte

ADR-0001 sépare raisonnement LLM et calcul déterministe, mais la première implementation de l'orchestrateur transmettait uniquement du texte. Le moteur n'était pas appelé par les agents, l'audit ne recevait aucun résultat déterministe et les validations différaient entre la CLI et les fonctions numériques.

## Décision

1. `DeterministicEngine` devient l'interface unique des opérations `budget`, `compare`, `paired` et `separate`.
2. Un agent peut rendre une enveloppe JSON optionnelle avec `message` et `calculation_requests`. Le texte simple reste accepté pour préserver les adapters existants.
3. Chaque demande produit un enregistrement `ok` ou `rejected`, transmis aux agents suivants sous `deterministic_calculations`.
4. Les sorties narratives antérieures sont sérialisées sous `untrusted_agent_response` et ne sont jamais présentées comme instructions ou sources.
5. Un plan avec `mandatory_final_audit=True` contient exactement un `METRO-AUDIT` placé en dernière étape.
6. Le module `validation` concentre les invariants numériques et métrologiques partagés par la CLI et le moteur.

## Conséquences

- ADR-0001 devient un comportement testable de bout en bout.
- Un calcul invalide reste visible sans interrompre toute l'orchestration.
- Les corrélations non nulles et les séparations conditionnelles exigent désormais une justification écrite.
- Le modèle actuel ne connaissant pas les unités des sensibilités, il refuse de combiner des unités de composantes différentes. Une future extension d'unités typées pourra remplacer cette restriction conservatrice.
- Le contexte n'est pas encore un dossier d'étude persistant : identifiant d'exécution, version, modèle LLM, coût et hash des prompts restent un chantier ultérieur.
