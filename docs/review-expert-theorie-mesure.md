# Revue de la première ébauche `expert-theorie-mesure`

**Verdict : VALIDÉ SOUS CONDITIONS**

La compétence constitue un bon socle conceptuel VIM/GUM pour THEORIA. Sa structure est valide, son déclenchement est suffisamment discriminant et ses garde-fous corrigent plusieurs confusions fréquentes. Elle ne constitue toutefois pas, à elle seule, une bibliothèque documentaire ni un moteur de calcul.

## Points forts

- part de l'usage et de la décision plutôt que de l'instrument ;
- accepte les modèles implicites `h(Y, X)=0` et explicites `Y=f(X)` ;
- exige provenance, unités, hypothèses et corrélations ;
- distingue correctement les méthodes d'évaluation de type A/B de la nature des effets ;
- interdit les hypothèses silencieuses d'indépendance, normalité, linéarité ou `k=2` ;
- préserve les données brutes et motive les exclusions ;
- sépare les responsabilités documentaire, conceptuelle, physique, logicielle et de curation ;
- écarte explicitement la théorie mathématique de la mesure de Lebesgue hors demande dédiée.

## Écarts importants

1. **Corpus incomplet.** R140, R113, R280, R353, R560 et R603 sont identifiées, mais leurs PDF n'ont pas été fournis. Aucune définition, formule ou conclusion issue du texte complet ne peut leur être attribuée.
2. **Calcul non exécutable.** La compétence prescrit une méthode sans fournir de moteur déterministe. METRO-MASTER comble cette frontière avec les modules Python et leurs tests.
3. **Comparaison de bancs peu développée.** Le socle général ne formalise pas la séparation `banc / référence / partagé / transfert / protocole`. Cette discipline reste portée par le contrat commun et METRO-COMPARE.
4. **Passage de relais non sérialisé.** Le contrat entre agents est juste, mais qualitatif. L'orchestrateur METRO-MASTER fournit l'ordre et le contexte ; un schéma JSON de dossier d'étude pourra être ajouté ultérieurement.

## Améliorations non bloquantes

- ajouter un ou deux cas validés avec données réelles anonymisées ;
- associer les références JCGM à leurs identifiants exacts et à une date de vérification ;
- formaliser une grille de choix entre propagation linéaire, Monte-Carlo et données de validation ;
- ajouter un format de sortie machine lisible pour les grandeurs, hypothèses et sources ;
- tester le comportement sur un cas ambigu, un cas non linéaire et une décision de conformité.

## Intégration réalisée

- compétence installée dans la bibliothèque locale Codex ;
- copie portable conservée dans `skills/expert-theorie-mesure/` ;
- invariants intégrés au prompt THEORIA et au contrat commun ;
- six fiches Techniques de l'Ingénieur ajoutées au catalogue avec `content_status = metadata_only` ;
- tests ajoutés pour vérifier la présence de ces limites dans le prompt et le catalogue.

