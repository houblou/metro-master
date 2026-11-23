# ADR-0007 — Intégration scientifique gouvernée et traces de calcul

- **Statut :** proposé
- **Date :** 2026-11-23
- **Version cible initiale :** 0.9.0
- **Décideur :** responsable MetrologyLab AI
- **Complète :** ADR-0001, ADR-0002, ADR-0004 et ADR-0006

## Contexte

MetrologyLab AI doit combler quatre familles de lacunes à partir de quatre dépôts réutilisables : unités et propagation avancée, expertise métrologique par grandeur, statistiques d'ingénierie, puis CMM/GD&T et métrologie dimensionnelle.

Les dépôts externes sont utiles mais ne peuvent pas devenir directement une autorité de calcul. Leur présence sur GitHub, leur popularité ou leur licence ne prouvent ni l'exactitude scientifique, ni l'applicabilité normative, ni la compatibilité avec le noyau déterministe. Le parcours actuel présente en outre quatre faiblesses avant extension :

1. les modules natifs ne publient pas systématiquement version d'algorithme, empreinte d'implémentation et jeu de validation ;
2. les calculs Monte-Carlo futurs exigent graine, générateur, versions numériques et diagnostic de convergence ;
3. un rôle autre que `MODEL-COMPILER` peut actuellement demander un calcul sans vérification complète de provenance ;
4. une orchestration peut se terminer avec une vérification de conclusion `unverified` sans être marquée comme échec de complétude.

## Décision

Adopter une intégration sélective, gouvernée et traçable :

1. **Geler chaque source externe** par dépôt, commit, chemin, empreinte de blob, licence et mode d'utilisation (`copy`, `adapt`, `reimplement`, `reference_only`).
2. **Ne jamais activer directement un script externe.** Les calculs publiables sont des modules natifs revus dans le dépôt ou des formules déjà gouvernées par `ModuleStore`.
3. **Conserver les licences tierces.** Toute copie ou adaptation substantielle sous MIT garde le copyright et le texte MIT ; les contenus du pack NIST gardent leur licence de pack, leur provenance et l'absence d'approbation.
4. **Ajouter un descripteur obligatoire à chaque module natif** : identifiant, version, type, domaine, références, empreinte d'implémentation, empreinte du jeu de validation et dépendances numériques.
5. **Créer une trace de calcul canonique** liant requête, preuves, hypothèses, module, environnement, configuration numérique, résultat, avertissements, refus et empreintes.
6. **Réserver l'autorité de compiler une demande issue du langage naturel à `MODEL-COMPILER`.** Les autres rôles proposent un modèle ou une méthode ; ils ne déclenchent pas un calcul publiable.
7. **Imposer une porte de complétude après `METRO-AUDIT`.** Une étude contenant un calcul réussi n'est jamais `VALIDÉE` si un claim manque, diverge ou reste `unverified`.
8. **Persister aussi les refus et les études incomplètes.** La porte de complétude change le verdict ; elle ne supprime jamais la trace.
9. **Préserver le noyau sans dépendance obligatoire.** Les bibliothèques numériques avancées sont placées derrière des adaptateurs optionnels, détectés explicitement et enregistrés dans la trace. Aucune dégradation silencieuse n'est permise.
10. **Charger les connaissances progressivement.** Les références par grandeur, statistiques ou CMM sont injectées seulement lorsque le routeur en démontre le besoin, afin de préserver les tokens de l'audit.

## Sources gelées pour la conception

| Source | Commit | Licence | Usage prévu |
|---|---|---|---|
| [`K-Dense-AI/scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) | [`c21d13b3cc2894680229ba9959a53281acb9200e`](https://github.com/K-Dense-AI/scientific-agent-skills/commit/c21d13b3cc2894680229ba9959a53281acb9200e) | MIT | unités, Monte-Carlo, plausibilité, tests et pratiques de restitution |
| [`K-Dense-AI/scientific-agents`](https://github.com/K-Dense-AI/scientific-agents) | [`98c7fae46648724e1a43a1f2b207b0c82fcc462e`](https://github.com/K-Dense-AI/scientific-agents/commit/98c7fae46648724e1a43a1f2b207b0c82fcc462e) | MIT | expertise métrologique par grandeur et contrôles professionnels |
| [`jgsystemsconsulting/jgs-se-knowledge-packs`](https://github.com/jgsystemsconsulting/jgs-se-knowledge-packs) | [`f0a8cf25e69859fdcb6d3ea2ff9a2c9751fb1df5`](https://github.com/jgsystemsconsulting/jgs-se-knowledge-packs/commit/f0a8cf25e69859fdcb6d3ea2ff9a2c9751fb1df5) | pack NIST : domaine public américain déclaré ; outillage : MIT | portes statistiques, méthodes et corpus de référence |
| [`MP-AI-20/mechanical-engineering-skills`](https://github.com/MP-AI-20/mechanical-engineering-skills) | [`50434c7cdfe93d132534b7375a4c1d2d81d5029d`](https://github.com/MP-AI-20/mechanical-engineering-skills/commit/50434c7cdfe93d132534b7375a4c1d2d81d5029d) | MIT | CMM, GD&T, surface, Gauge R&R industriel et repères |

Ces quatre empreintes ont été vérifiées sur GitHub le 2026-11-23. Le registre d'import devra conserver ces commits et les empreintes des fichiers réellement utilisés. Aucun texte ISO, ASME ou AIAG sous droits n'est importé par transitivité.

## Options considérées

### A — Copier les quatre dépôts dans le projet

| Dimension | Évaluation |
|---|---|
| Vitesse initiale | élevée |
| Cohérence avec le noyau | faible |
| Traçabilité | faible sans refonte |
| Maintenance | très coûteuse |
| Risque scientifique et licences transitives | élevé |

**Rejetée :** interfaces divergentes, dépendances lourdes, duplication de prompts et autorité de calcul mal définie.

### B — Importer seulement les prompts

| Dimension | Évaluation |
|---|---|
| Vitesse initiale | élevée |
| Capacité numérique | très faible |
| Risque d'hallucination de résultats | élevé |
| Testabilité | faible |

**Rejetée :** améliore le discours sans combler les calculateurs manquants.

### C — Adapter les connaissances et réimplémenter les noyaux revus

| Dimension | Évaluation |
|---|---|
| Vitesse initiale | moyenne |
| Cohérence avec le noyau | élevée |
| Traçabilité | élevée |
| Maintenance | maîtrisable |
| Validation indépendante | possible |

**Retenue :** les dépôts externes deviennent des sources de conception et de tests ; l'autorité numérique reste dans le moteur revu.

### D — Charger des plugins Python externes à l'exécution

| Dimension | Évaluation |
|---|---|
| Puissance | très élevée |
| Isolation | insuffisante sans worker |
| Reproductibilité | variable |
| Surface d'attaque | élevée |

**Différée :** un worker signé et isolé demanderait une décision séparée. Il n'est pas nécessaire pour les modules natifs livrés et revus avec le cœur.

## Conséquences

### Positives

- chaque résultat peut être relié à ses entrées, preuves, algorithme, environnement et validations ;
- les quatre sources renforcent le produit sans déplacer l'autorité scientifique vers un prompt externe ;
- les anciennes opérations `budget`, `compare`, `paired` et `separate` restent compatibles ;
- les dépendances avancées restent optionnelles et leurs absences produisent un refus explicite ;
- l'audit final devient une vraie porte de sortie.

### Négatives

- l'intégration complète nécessite plusieurs versions et un corpus de référence conséquent ;
- la reproductibilité Monte-Carlo impose de figer générateur, graine et versions numériques ;
- les modules natifs devront porter plus de métadonnées et les anciens enregistrements devront être migrés ou lus en compatibilité ;
- les références par grandeur augmentent le volume documentaire, ce qui impose un chargement progressif strict.

## Critères d'acceptation de l'ADR

- [ ] approbation du responsable MetrologyLab AI ;
- [ ] registre de sources et licences validé ;
- [ ] schéma de trace relu par un métrologue ;
- [ ] décision sur les dépendances et versions Python du profil scientifique ;
- [ ] jeux de référence indépendants identifiés pour chaque module ;
- [ ] aucun conflit avec les documents privés ou les normes non redistribuables.
