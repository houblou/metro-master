# Plan complet d'intégration des quatre sources scientifiques

- **Statut :** en cours — lots 0 et 1 livrés dans la version 0.9.0
- **Date de référence :** 2026-11-23
- **Point de départ :** MetrologyLab AI 0.8.0, 86 tests réussis
- **État d'exécution :** MetrologyLab AI 0.9.0, 98 tests réussis, lot actif : grandeurs et unités
- **Décision d'architecture :** [ADR-0007](adr/0007-integration-scientifique-gouvernee-et-traces.md)
- **Objectif final :** intégrer les apports utiles des quatre dépôts sans perdre la séparation LLM/calcul, la compatibilité, les licences, la reproductibilité ni la traçabilité.

## 1. Résultat attendu

À la fin du programme, une demande métrologique suit toujours ce parcours :

```text
demande + documents + données
          │
          ▼
 cadrage et routage borné
          │
          ▼
spécialistes → proposition de modèle/méthode
          │
          ▼
 MODEL-COMPILER → preuves par champ
          │
          ▼
 porte de provenance et d'unités
          │ refus visible si incomplète
          ▼
 DeterministicEngine
          │
          ├── résultat numérique
          └── trace canonique signée par empreinte
          │
          ▼
 revue GUM/DATA/PHYS/CALIB utile
          │
          ▼
 METRO-AUDIT + claims structurés
          │
          ▼
 porte de complétude
          │
          ├── VALIDÉ / VALIDÉ SOUS CONDITIONS
          └── INCOMPLET / NON VALIDE
          │
          ▼
 StudyStore append-only + rapport
```

Le parcours ne doit jamais convertir automatiquement une connaissance, un prompt ou un script tiers en résultat publiable.

## 2. État actuel et défauts à fermer

### Ce qui fonctionne

- 86 tests automatisés passent sous la version 0.8.0 ;
- le routeur place `MODEL-COMPILER` avant les experts qui examinent les résultats et impose `METRO-AUDIT` en dernier ;
- le moteur calcule correctement le budget corrélé de référence ;
- `StudyStore` détecte une modification de révision ;
- les connaissances candidates et les modules candidats ne sont pas activés automatiquement ;
- le budget de tokens conserve une réserve pour l'audit.

### Défauts constatés

| ID | Défaut | Risque | Correction obligatoire |
|---|---|---|---|
| D1 | un rôle tel que `GUM-EXPERT` peut encore émettre directement une `calculation_request` | valeur non couverte par les preuves de `MODEL-COMPILER` | autorité de calcul agent limitée à `MODEL-COMPILER` |
| D2 | l'exemple bout en bout termine avec `conclusion_verification.status = unverified` | parcours techniquement terminé mais résultat non vérifié | porte de complétude après audit |
| D3 | les modules natifs n'exposent pas tous version, empreinte d'implémentation et jeu de validation | résultat impossible à reproduire à long terme | descripteur natif obligatoire |
| D4 | la sortie CLI d'un calcul ne contient pas d'enveloppe de trace | calcul isolé difficile à rattacher à une étude | mode de sortie traçable et option `--trace-out` |
| D5 | l'analyse dimensionnelle du registre de formules et le modèle d'unités des budgets sont séparés | incohérences futures | module unique de grandeurs et adaptateurs d'unités |
| D6 | aucune couverture de code, mutation, sécurité ou matrice multi-OS n'est mesurée | défauts invisibles malgré 86 tests | nouvelle stratégie CI |
| D7 | aucune provenance de licence n'est vérifiée automatiquement pour les capacités importées | redistribution non maîtrisée | registre de sources avec contrôle CI |

Les défauts D1 à D5 sont bloquants avant l'activation d'un nouveau calcul.

### Preuve de l'audit initial

Contrôles exécutés sur la version 0.8.0 le 2026-11-23 :

```text
python -m unittest discover -s tests -v
→ 86 tests exécutés, 86 réussis

python examples/run_structured_backend.py
→ route : METRO-MASTER → THEORIA → MODEL-COMPILER → GUM-EXPERT → METRO-AUDIT
→ calcul : status=ok, provenance_checked=false
→ conclusion : status=unverified, uncovered_calculation_ids=[demo-budget]
```

Verdict de câblage initial : le routage et le moteur historique fonctionnent, mais le parcours n'est pas encore acceptable pour une conclusion publiable. Les défauts D1 et D2 prouvent qu'un calcul peut contourner la compilation probante puis rester non couvert par l'audit final. Le lot 1 doit rendre ce scénario impossible par construction.

## 3. Registre d'acquisition des quatre sources

### 3.1 K-Dense Scientific Agent Skills

- dépôt : `K-Dense-AI/scientific-agent-skills` ;
- commit de conception : `c21d13b3cc2894680229ba9959a53281acb9200e` ;
- licence : MIT ;
- cible principale : `skills/uncertainty-and-units` ;
- actifs examinés : `SKILL.md`, sept références, sept scripts et deux suites de tests ;
- mode par défaut : `adapt` pour les instructions, `reimplement` pour les noyaux, `copy` seulement pour un test ou utilitaire clairement isolé et attribué.

Apports :

1. conversions et dimensions physiques ;
2. propagation analytique et Monte-Carlo ;
3. corrélations et paramètres ajustés ;
4. plausibilité physique et ordres de grandeur ;
5. règles de restitution et arrondis ;
6. audit de code qui perd les unités ;
7. tests de régression des scripts scientifiques.

Ne pas reprendre sans revue : versions de dépendances, CLI externe, hypothèses implicites, listes de constantes et exemples non reliés à une source primaire.

### 3.2 K-Dense Scientific Agents

- dépôt : `K-Dense-AI/scientific-agents` ;
- commit de conception vérifié : `98c7fae46648724e1a43a1f2b207b0c82fcc462e` ;
- licence : MIT ;
- cible : profil `metrology-scientist` ;
- mode : `adapt` en français, puis validation documentaire.

Apports :

- classification des travaux métrologiques ;
- traçabilité et chaîne d'étalonnage ;
- décision de conformité et risques ;
- CMC, comparaisons, CRM et métrologie légale ;
- crochets par grandeur : masse, force, électricité, temps, température, pression, chimie, photométrie, rayonnements, débit, humidité.

Destination : références progressives chargées par `THEORIA`, `PHYS-METRO`, `CALIB-EXPERT` et `NORM-EXPERT`. Aucun nouveau rôle permanent n'est créé uniquement pour ces textes.

### 3.3 NIST Statistical Handbook pack

- dépôt : `jgsystemsconsulting/jgs-se-knowledge-packs` ;
- commit : `f0a8cf25e69859fdcb6d3ea2ff9a2c9751fb1df5` ;
- licence : contenu du pack déclaré domaine public américain ; outillage MIT ;
- actifs : `LICENSE`, `PACK.yaml`, `SKILL.md`, huit chapitres, glossaire, patrons et aide-mémoire ;
- mode : `adapt` pour la méthode, `reference_only` pour les passages nécessitant une source officielle, `reimplement` pour les calculateurs.

Apports numériques ordonnés :

1. EDA et diagnostic des quatre hypothèses ;
2. caractérisation d'un processus de mesure ;
3. Gauge R&R et ANOVA ;
4. stabilité, cartes et capabilité ;
5. régression et diagnostics de résidus ;
6. DOE ;
7. comparaisons de groupes ;
8. fiabilité.

Pour les jeux gold, privilégier les jeux NIST officiels réellement accessibles. Le pack est une carte de méthode, pas une preuve indépendante de chaque résultat.

### 3.4 MP-AI-20 Mechanical Engineering Skills

- dépôt : `MP-AI-20/mechanical-engineering-skills` ;
- commit : `50434c7cdfe93d132534b7375a4c1d2d81d5029d` ;
- licence : MIT ;
- actifs : `skills/metrology/SKILL.md` et `vault_notes.json` ;
- mode : `adapt` et `reimplement` ; jamais de copie d'un contenu normatif tiers.

Apports : CMM, repères, stratégie de palpage, GD&T, état de surface, thermique dimensionnelle, Gauge R&R industriel et hiérarchie d'étalonnage.

Limite : les références à ISO 10360, ISO 1101, ASME Y14.5, AIAG MSA ou documents similaires ne donnent aucun droit de reproduire leurs clauses, tableaux ou figures. Sans texte autorisé, MetrologyLab AI fournit un plan ou une métadonnée, pas une exigence normative détaillée.

## 4. Méthode d'acquisition gouvernée

Chaque actif suit les onze étapes suivantes :

1. **Identifier** le besoin fonctionnel exact et le défaut qu'il corrige.
2. **Geler** dépôt, commit, chemin et SHA du blob.
3. **Qualifier la licence** du dépôt, du sous-dossier, du fichier et des contenus tiers cités.
4. **Choisir le mode** : copie, adaptation, réimplémentation ou référence seulement.
5. **Créer un enregistrement de source** avant toute modification du code.
6. **Extraire les invariants scientifiques**, séparément de la formulation du prompt.
7. **Comparer aux ADR et au noyau existant** pour éviter une seconde autorité de calcul.
8. **Implémenter derrière les contrats internes**, sans exécuter le code tiers non revu.
9. **Valider sur des cas indépendants**, pas seulement sur les tests de la source.
10. **Relire licence, sécurité et métrologie** avant activation.
11. **Promouvoir explicitement** la capacité et enregistrer sa version active.

### Enregistrement minimal d'une source

```json
{
  "schema_version": 1,
  "source_id": "kdense-uncertainty-units",
  "repository": "K-Dense-AI/scientific-agent-skills",
  "commit": "c21d13b3cc2894680229ba9959a53281acb9200e",
  "path": "skills/uncertainty-and-units/SKILL.md",
  "blob_sha": "28bcc333961e29f41681a7b7afdd01f402d54646",
  "license": "MIT",
  "usage_mode": "adapt",
  "local_targets": ["skills/metrology-lab-ai/references/units-and-monte-carlo-fr.md"],
  "modifications": "Synthèse française et adaptation aux portes de preuve MetrologyLab AI",
  "review_status": "candidate",
  "reviewed_by": null
}
```

Le contrôle CI refuse un actif tiers local sans enregistrement et refuse un enregistrement dont le commit, la licence ou les cibles manquent.

## 5. Architecture cible

### 5.1 Modules à créer ou approfondir

| Module | Responsabilité | Ne doit pas faire |
|---|---|---|
| `source_registry.py` | licences, commits, blobs, modes d'usage et validations | télécharger ou exécuter automatiquement une source |
| `quantities.py` | dimensions, unités, conversions et coefficients de sensibilité | choisir silencieusement une unité ou une convention |
| `trace.py` | canonicalisation, empreintes et trace de calcul | déclarer un modèle scientifiquement valide |
| `native_modules.py` ou paquet `scientific_modules/` | descripteurs et calculateurs revus | charger du Python arbitraire |
| `study_execution.py` | état du parcours, transitions et porte de complétude | produire des résultats numériques |
| `validation.py` | invariants transversaux | mélanger validation normative et arithmétique |
| `orchestrator.py` | routage et coordination de haut niveau | porter tous les sous-parcours et états internes |

### 5.2 Descripteur d'un module natif

Chaque opération native expose au minimum :

- `module_id`, `module_version`, `kind=native` ;
- titre, domaine, unités et limites validées ;
- identifiant d'algorithme et `implementation_sha256` ;
- sources primaires et actifs externes utilisés ;
- `validation_suite_sha256` ;
- dépendances et versions compatibles ;
- déterminisme exact ou déterminisme conditionné par une graine ;
- schémas d'entrée et de sortie ;
- avertissements et refus possibles.

`ModuleRegistry.describe()` rend ces informations. Le moteur les copie dans chaque trace ; le résultat scientifique ne doit pas fabriquer lui-même ces métadonnées.

### 5.3 Trace canonique d'un calcul

```json
{
  "trace_schema_version": 1,
  "trace_id": "calc-...",
  "study_id": "study-...",
  "request_id": "rr-pressure-001",
  "request_sha256": "...",
  "payload_sha256": "...",
  "operation": "gauge-rr",
  "module": {
    "id": "gauge-rr",
    "version": "1.0.0",
    "kind": "native",
    "implementation_sha256": "...",
    "validation_suite_sha256": "..."
  },
  "engine": {
    "metrology_lab_ai_version": "0.x.y",
    "python_version": "...",
    "dependencies": {"numpy": "..."}
  },
  "evidence": [
    {
      "field_path": "/measurements/0/value",
      "source_ref": "user_request",
      "source_sha256": "...",
      "excerpt_sha256": "...",
      "evidence_type": "provided"
    }
  ],
  "assumptions": [],
  "execution": {
    "deterministic": true,
    "seed": null,
    "rng": null,
    "tolerances": {},
    "convergence": null
  },
  "status": "ok",
  "result_sha256": "...",
  "warnings": [],
  "previous_trace_sha256": "...",
  "trace_sha256": "..."
}
```

Règles :

- la requête et le résultat sont sérialisés en JSON canonique avant empreinte ;
- les timestamps appartiennent à la trace, jamais au hash du résultat scientifique ;
- Monte-Carlo enregistre graine, algorithme RNG, nombre de tirages, lots, critère et diagnostic de convergence ;
- une empreinte prouve l'intégrité depuis la capture, pas la vérité de la source ;
- les traces d'une étude forment une chaîne ; `StudyStore` conserve aussi leur ensemble dans la révision ;
- la CLI imprime l'enveloppe de trace et n'écrit un fichier que sur demande explicite.

## 6. Parcours orchestrateur sans défaut silencieux

### États proposés

| État | Artefact requis pour sortir | Échec visible |
|---|---|---|
| `intake` | décision, mesurande, unité/domaine ou liste des manques | demande vide ou ambiguïté bloquante |
| `evidence_ready` | sources accessibles et empreintes | métadonnée seule présentée comme contenu |
| `model_proposed` | modèle, méthode, hypothèses et influences | modèle non identifiable |
| `compiled` | requêtes avec preuves de chaque champ critique | valeur inventée ou preuve absente |
| `validated` | unités, domaine, plan et invariants acceptés | incohérence dimensionnelle/statistique |
| `executed` | résultat ou refus + trace | module/dépendance indisponible |
| `reviewed` | diagnostic du spécialiste adapté | hypothèse critique non examinée |
| `audited` | claims structurés et couverture de tous les calculs | claim divergent ou absent |
| `persisted` | révision chaînée | rupture d'intégrité |

### Autorités

- les spécialistes produisent texte, modèles et propositions ;
- `MODEL-COMPILER` est le seul rôle agent qui peut émettre une requête de calcul publiable issue du langage naturel ;
- la CLI peut soumettre directement une requête JSON, marquée `structured_input` ;
- `DeterministicEngine` est la seule autorité numérique ;
- `METRO-AUDIT` est la seule conclusion finale agent ;
- `CompletionGate` est l'autorité déterministe du statut final.

### Porte de complétude

Le statut final est automatiquement :

- `NON VALIDE` si un claim diverge, si une trace est invalide ou si un calcul critique est rejeté ;
- `INCOMPLET` si un calcul réussi n'est pas couvert par un claim, si l'audit manque, si une preuve critique manque ou si un rôle obligatoire a été retiré par le budget ;
- `VALIDÉ SOUS CONDITIONS` si tous les calculs sont vérifiés mais que des hypothèses ou limites déclarées conditionnent la décision ;
- `VALIDÉ` seulement si calculs, claims, traces et prérequis sont complets et sans réserve bloquante.

Une étude `INCOMPLET` ou `NON VALIDE` est tout de même sauvegardée.

## 7. Lots d'implémentation

### Lot 0 — Gouvernance des sources et baseline (0.8.x)

- [x] ajouter le registre de sources, les quatre commits et les licences ;
- [x] compléter `THIRD_PARTY_NOTICES.md` et déclarer les modes d'usage ;
- [x] automatiser l'absence de contenu privé et la couverture de chaque actif tiers déclaré ;
- [x] geler les 86 tests existants comme baseline ;
- [x] vérifier localement la structure, les empreintes gelées et les cibles du registre d'acquisition.

**Sortie :** aucune capacité nouvelle, mais aucune acquisition ne peut contourner les licences.

### Lot 1 — Trace et parcours obligatoire (0.9.0)

- [x] implémenter les descripteurs natifs ;
- [x] ajouter `CalculationTrace` et la chaîne des traces ;
- [x] rendre la provenance obligatoire pour les calculs agents ;
- [x] refuser les calculs agents hors `MODEL-COMPILER` ;
- [x] implémenter la porte de complétude ;
- [x] corriger l'exemple structuré pour obtenir une vérification `verified` ;
- [x] conserver la lecture des requêtes et études historiques v1.

**Sortie :** les quatre opérations existantes deviennent totalement traçables avant toute extension.

### Lot 2 — Grandeurs et unités (0.10.0)

- [ ] réunir l'algèbre dimensionnelle du registre et les unités des budgets — conversions de budget livrées, registre déclaratif restant à migrer ;
- [ ] définir un adaptateur interne minimal et un adaptateur Pint optionnel — adaptateur minimal livré, adaptateur optionnel restant ;
- [x] gérer conversions multiplicatives, unités dérivées et températures avec décalage ;
- [ ] typer les coefficients de sensibilité ;
- [x] refuser unités inconnues, ambiguës, logarithmiques ou contextuelles non configurées ;
- [x] vérifier l'invariance des résultats sous conversion cohérente.

**Sortie :** plus de comparaison naïve de chaînes d'unités dans le budget.

### Lot 3 — Monte-Carlo JCGM 101 (0.11.0)

- [ ] ajouter distributions prises en charge avec paramètres explicites ;
- [ ] échantillonner les corrélations via une méthode numérique validée ;
- [ ] figer générateur et graine ;
- [ ] exécuter en lots bornés ;
- [ ] calculer estimateur, incertitude, intervalle de couverture et asymétrie utile ;
- [ ] tester la convergence et comparer au GUM linéaire lorsque applicable ;
- [ ] refuser une conclusion JCGM 101 sans stabilité numérique démontrée.

**Sortie :** modèles non linéaires ou non gaussiens calculés et reproductibles.

### Lot 4 — Statistiques d'ingénierie (0.12.0 à 0.14.0)

Ordre d'activation :

1. `eda-diagnostics` et statistiques descriptives ;
2. `gauge-rr-crossed` puis variantes justifiées ;
3. `spc-shewhart` avec phases I/II ;
4. `process-capability` conditionné par la stabilité ;
5. `linear-regression` et diagnostics ;
6. `anova` et comparaisons multiples ;
7. `doe` puis fiabilité.

Chaque module possède son contrat de plan. Par exemple, `gauge-rr-crossed` refuse l'absence de pièces, opérateurs, répétitions ou identifiabilité ; `process-capability` refuse un procédé déclaré instable ou sans limites de spécification.

### Lot 5 — Expertise par grandeur (0.15.0)

- [ ] créer des références françaises courtes par grandeur ;
- [ ] router seulement les références nécessaires ;
- [ ] distinguer faits métrologiques, pratiques, textes normatifs et choix de modèle ;
- [ ] relier chaque règle critique à une source accessible ;
- [ ] ajouter des scénarios masse, température, pression, électricité, débit et chimie.

**Sortie :** couverture métier plus large sans treize prompts chargés simultanément.

### Lot 6 — CMM, GD&T et surface (0.16.0)

- [ ] ajouter le cadrage CMM, repères, palpage, thermique et stratégie de mesure ;
- [ ] réutiliser les calculateurs transversaux de R&R et d'unités ;
- [ ] séparer vérification géométrique et décision normative ;
- [ ] exiger un extrait autorisé pour toute clause ou limite issue d'une norme ;
- [ ] créer des exemples synthétiques sans reproduire de tableaux propriétaires.

**Sortie :** assistance dimensionnelle industrielle, limitée par les textes réellement accessibles.

### Lot 7 — Durcissement et version 1.0

- [ ] benchmarks gold publics ;
- [ ] couverture et mutation ;
- [ ] CI Windows, Linux et macOS ;
- [ ] CodeQL, analyse de dépendances et SBOM ;
- [ ] comparaison à un calcul indépendant ;
- [ ] revue métrologique externe ;
- [ ] documentation française et anglaise minimale ;
- [ ] migration et rollback démontrés.

## 8. Stratégie de tests

### Pyramide

| Niveau | Cible | Exemples |
|---|---|---|
| unitaires | nombreux, rapides | unités, canonicalisation, hashes, formules, distributions, indices |
| contrats | interfaces stables | enveloppe agent, descripteur natif, trace, compatibilité v1 |
| intégration | modules assemblés | compiler → validation → moteur → trace → audit |
| bout en bout | parcours décisionnels | pression, Monte-Carlo, R&R, capabilité, CMM |
| gold/benchmark | exactitude indépendante | exemples JCGM/NIST et calculs manuels |

### Cas de parcours obligatoires

1. **Budget corrélé linéaire** : reproduire le résultat actuel et sa décomposition, avec trace complète.
2. **Modèle non linéaire** : Monte-Carlo stable, graine fixée, répétition bit-à-bit dans l'environnement figé et intervalle cohérent.
3. **Gauge R&R croisé** : plan complet, décomposition et refus si une dimension du plan manque.
4. **SPC puis capabilité** : calcul de capabilité bloqué tant que la stabilité n'est pas établie.
5. **CMM thermique** : conversions cohérentes, correction et incertitude ; refus d'une unité ambiguë.
6. **Norme inaccessible** : métadonnée conservée mais aucune clause inventée.
7. **Budget de tokens serré** : spécialistes secondaires omis, trace et audit final conservés.
8. **Claim erroné** : verdict déterministe `NON VALIDE`.
9. **Claim absent** : verdict `INCOMPLET`, jamais succès silencieux.
10. **Registre altéré** : source, module, trace ou étude refusés au chargement.

### Tests de propriétés

- invariance d'un résultat sous conversion d'unités cohérente ;
- invariance à la permutation des observations lorsque le plan le permet ;
- variance non négative et matrices admissibles ;
- conservation des sommes de carrés ANOVA ;
- monotonie attendue des indices sous variation contrôlée ;
- stabilité des résultats Monte-Carlo sous augmentation des tirages dans la tolérance annoncée ;
- sérialisation canonique identique pour des dictionnaires d'ordre différent.

### Cibles mesurables

- 100 % des calculs réussis ont une trace et un descripteur de module ;
- 100 % des champs numériques critiques issus du langage naturel ont une preuve ;
- 100 % des actifs tiers ont licence, commit, blob et cible locale ;
- 100 % des calculs réussis sont couverts par les claims finaux ;
- couverture de lignes ≥ 90 % sur le noyau et ≥ 95 % sur les modules scientifiques ;
- couverture de branches ≥ 85 % sur validation, trace et portes ;
- score de mutation cible ≥ 80 % sur les formules critiques ;
- zéro test réseau dans les calculateurs ;
- zéro accès fichier hors racines gouvernées.

## 9. Matrice CI cible

| Job | Plateformes | Python | Dépendances |
|---|---|---|---|
| cœur minimal | Ubuntu, Windows, macOS | 3.11, 3.12, 3.14 | aucune optionnelle |
| scientifique | Ubuntu, Windows | versions supportées par NumPy/SciPy/Pint | extra figé |
| compatibilité | Ubuntu | plus ancienne version supportée | lecture anciens artefacts |
| sécurité | Ubuntu | version courante | CodeQL, Bandit ou équivalent, audit dépendances |
| licence | Ubuntu | version courante | registre, notices, fichiers interdits |
| packaging | Ubuntu, Windows | version courante | wheel, sdist, installation du skill |

Le choix exact des versions Pint, uncertainties, NumPy et SciPy est un livrable du spike de compatibilité. Les versions proposées par K-Dense ne sont pas adoptées avant réussite de cette matrice.

## 10. Données, dépendances et tokens

### Données

- jeux synthétiques versionnés pour les refus et invariants ;
- jeux publics NIST/JCGM avec provenance et empreinte ;
- données de laboratoire uniquement anonymisées et hors dépôt public si leur diffusion n'est pas autorisée ;
- aucune norme payante ni ressource personnelle dans les fixtures publiques.

### Dépendances

- cœur minimal sans dépendance obligatoire ;
- extra scientifique explicitement installé ;
- absence de l'extra = `DependencyUnavailable`, jamais résultat simplifié ;
- versions et lockfile enregistrés dans la trace ou son environnement de release ;
- SBOM généré à chaque release scientifique.

### Tokens

- les méthodes numériques restent hors prompt et dans le moteur ;
- les références sont découpées par sujet et chargées à la demande ;
- le contexte transmet des traces compactes, puis des détails seulement sur demande de l'audit ;
- les profils `eco`, `standard`, `deep` conservent une réserve finale ;
- un profil ne peut retirer `MODEL-COMPILER`, le moteur, la porte de complétude ou `METRO-AUDIT` lorsqu'un résultat numérique est demandé.

## 11. Fichiers prévus

```text
src/metro_master/
  source_registry.py
  trace.py
  quantities.py
  study_execution.py
  scientific_modules/
    descriptors.py
    monte_carlo.py
    statistics.py
    cmm.py
src/metro_master/resources/
  source-manifest.json
  schemas/
    calculation-trace.schema.json
    source-asset.schema.json
third_party/
  licenses/
  source-records/
skills/metrology-lab-ai/references/
  units-and-monte-carlo-fr.md
  statistics/
  domains/
  dimensional-metrology-fr.md
tests/
  gold/
  journeys/
  test_source_registry.py
  test_trace.py
  test_study_execution.py
  test_quantities.py
  test_monte_carlo.py
  test_engineering_statistics.py
```

Les noms peuvent être ajustés avant implémentation, mais les responsabilités et les portes ne doivent pas être fusionnées dans `orchestrator.py`.

## 12. Revue et promotion

Une capacité ne devient active que si :

1. licence et provenance sont complètes ;
2. schémas d'entrée/sortie sont stables ;
3. cas nominaux, limites et refus passent ;
4. deux références indépendantes concordent lorsque possible ;
5. la trace est complète ;
6. le parcours bout en bout termine avec des claims `verified` ;
7. le module ne contourne pas `DeterministicEngine` ;
8. la documentation indique domaine, hypothèses et limites ;
9. un approbateur humain autorise l'activation ;
10. un rollback vers la version précédente est testé.

## 13. Ordre recommandé et dépendances

```text
Lot 0 Sources/licences
        │
        ▼
Lot 1 Trace + parcours obligatoire
        │
        ▼
Lot 2 Grandeurs/unités
        │
        ├──────────────┐
        ▼              ▼
Lot 3 Monte-Carlo   Lot 4 Statistiques
        │              │
        └──────┬───────┘
               ▼
      Lot 5 Expertise par grandeur
               │
               ▼
       Lot 6 CMM/GD&T/surface
               │
               ▼
         Lot 7 Durcissement 1.0
```

Commencer par les statistiques ou Monte-Carlo avant les lots 0 à 2 créerait des résultats impossibles à tracer correctement et multiplierait les modèles d'unités.

## 14. Définition de terminé du programme

Le programme est terminé lorsque :

- les quatre sources apparaissent dans le registre avec licence et empreintes ;
- aucun contenu tiers non déclaré n'est distribué ;
- les opérations historiques restent compatibles ;
- unités, Monte-Carlo, statistiques prioritaires et parcours CMM utilisent le même moteur et la même trace ;
- chaque étude numérique suit compilation, validation, exécution, audit, porte de complétude et persistance ;
- aucun résultat `unverified` n'est présenté comme succès ;
- les rapports exposent module, version, hypothèses, sources, environnement, empreintes et limites ;
- la matrice CI et les benchmarks gold passent ;
- le responsable métrologique approuve le domaine d'emploi ;
- la release 1.0 peut être reconstruite depuis un checkout propre et son SBOM.

## 15. Action en cours

Les lots 0 et 1 sont livrés dans la version 0.9.0 : registre de sources, notices, descripteurs natifs, trace canonique, autorité de `MODEL-COMPILER`, porte de complétude, alias publics et tests sans installation. Le **lot 2 — grandeurs et unités** devient le prochain lot actif ; Monte-Carlo et statistiques restent bloqués tant que ce socle dimensionnel commun n'est pas terminé.
