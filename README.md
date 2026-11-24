# MetrologyLab AI

[![PyPI](https://img.shields.io/pypi/v/metrology-lab-ai)](https://pypi.org/project/metrology-lab-ai/)
[![Python](https://img.shields.io/pypi/pyversions/metrology-lab-ai)](https://pypi.org/project/metrology-lab-ai/)
[![Tests](https://github.com/houblou/metrology-lab-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/houblou/metrology-lab-ai/actions/workflows/tests.yml)
[![License](https://img.shields.io/github/license/houblou/metrology-lab-ai)](LICENSE)

MetrologyLab AI est un assistant métrologique Python open source, distribué sous licence Apache-2.0, pour construire des bilans d'incertitude traçables, comparer des moyens de mesure et préparer des rapports auditables. Il associe ChatGPT ou un autre LLM à treize agents spécialisés, un RAG vectoriel gouverné, une recherche Internet traçable, un registre d'études persistant et un noyau de calcul déterministe extensible. Sa priorité est la caractérisation d'un banc par comparaison : il conserve séparément l'incertitude du banc, celle de la référence, les effets partagés/corrélés et l'incertitude propre au protocole de comparaison.

Le nom public est cohérent de bout en bout : distribution PyPI et projet **MetrologyLab AI**, paquet importable `metrology_lab_ai` et commande `metrology-lab-ai`. Le module et la commande historiques `metro_master` / `metro-master`, ainsi que le rôle interne `METRO-MASTER`, restent disponibles afin de ne pas casser les intégrations existantes.

Le projet ne contient le texte intégral d'aucune norme ISO ni d'aucun article payant. Le catalogue documentaire fourni est un index de métadonnées et de liens officiels vérifiés le 5 novembre 2026. Un agent ne peut citer une exigence ou un numéro de clause que si le texte ou l'extrait correspondant lui a effectivement été fourni.

## Ce qui est livré

- treize rôles : `METRO-MASTER`, `PDF-EXTRACTOR`, `WEB-RESEARCHER`, `THEORIA`, `GUM-EXPERT`, `METRO-COMPARE`, `CALIB-EXPERT`, `DATA-METRO`, `MODEL-COMPILER`, `PHYS-METRO`, `NORM-EXPERT`, `MODULE-BUILDER`, `METRO-AUDIT` ;
- la compétence Codex portable `skills/expert-theorie-mesure`, importée et utilisée comme socle renforcé de THEORIA ;
- un contrat scientifique commun et des instructions spécialisées composables en prompts complets ;
- un prompt maître Markdown directement modifiable et trois profils de budget de tokens ;
- un catalogue documentaire structuré JCGM/BIPM, ISO, ILAC, EA et EURAMET ;
- propagation linéaire avec unités de sensibilité typées, conversions dimensionnelles, matrice de corrélation, contributions de covariance, incertitude élargie et Welch–Satterthwaite lorsque les composantes à degrés de liberté finis restent indépendantes ;
- calcul d'écart corrélé, score zêta, erreur normalisée, statistiques de paires et séparation conditionnelle de la variance du banc ;
- un orchestrateur Python indépendant du fournisseur de modèle ;
- un contrat `ResearchProvider` pour mener jusqu'à trois passes Web, filtrer les domaines et privilégier les sources officielles/primaires ;
- une mémoire `KnowledgeStore` intègre où sources Web, lots PDF et inférences restent candidates jusqu'à validation humaine ;
- un RAG hybride avec index vectoriel persistant, filtré sur les seules connaissances validées ;
- `MODEL-COMPILER`, qui transforme un texte libre en requête de calcul seulement si chaque nombre possède une preuve vérifiable ;
- un contrôle automatique des valeurs et unités reprises dans la conclusion finale, suivi d'une porte de complétude déterministe ;
- une trace canonique de chaque calcul réussi ou rejeté : preuves, hypothèses, module, version, empreintes, environnement et résultat ;
- un `StudyStore` append-only dont les révisions forment une chaîne SHA-256 ;
- des exports en rapport technique, projet de certificat non officiel et aide à la revue d'accréditation ;
- un contrat JSON optionnel qui relie les demandes des agents au moteur puis transmet les résultats déterministes à l'auditeur ;
- des exemples JSON, des tests et une documentation d'architecture/audit.

## Installation et vérification

Installation depuis PyPI :

```powershell
python -m pip install metrology-lab-ai
metrology-lab-ai --version
```

Les extensions restent facultatives : `metrology-lab-ai[units]` ajoute Pint et `metrology-lab-ai[pdf]` ajoute l'extraction PDF.

Installation depuis les sources :

```powershell
git clone https://github.com/houblou/metrology-lab-ai.git
cd metrology-lab-ai
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m unittest discover -s tests -t . -v
```

Depuis un checkout, les tests peuvent aussi être lancés sans installation ni `PYTHONPATH` avec `python -m unittest discover -s tests -t . -v`.

Le noyau n'a aucune dépendance d'exécution externe. Python 3.11 ou plus récent suffit. Un adaptateur Pint est disponible en option pour les intégrations qui ont besoin d'un registre d'unités plus large :

```powershell
python -m pip install -e ".[units]"
```

L'extraction de PDF est optionnelle et utilise `pypdf` :

```powershell
python -m pip install -e ".[pdf]"
```

### Installer le skill MetrologyLab AI

Le dépôt contient une compétence Agent Skills autonome dans `skills/metrology-lab-ai` et un manifeste de plugin dans `.codex-plugin/plugin.json`. L'installation par un gestionnaire compatible Agent Skills se fait depuis GitHub :

```powershell
npx skills add houblou/metrology-lab-ai --skill metrology-lab-ai
```

Installation locale manuelle pour Codex sous Windows :

```powershell
Copy-Item -Recurse -Force skills\metrology-lab-ai "$env:USERPROFILE\.codex\skills\metrology-lab-ai"
```

La compétence apporte les instructions françaises, les références statistiques et le pont portable. Pour exécuter les calculs déterministes, conserver aussi le dépôt ou installer le paquet Python. Le pont accepte `METRO_MASTER_PROJECT_ROOT` ou `--project-root` et ne contient aucun chemin personnel.

Afficher la version réellement installée :

```powershell
metrology-lab-ai --version
# alias historique : metro-master --version
```

La documentation navigable est publiée sur [houblou.github.io/metrology-lab-ai](https://houblou.github.io/metrology-lab-ai/) et le paquet sur [PyPI](https://pypi.org/project/metrology-lab-ai/).
Le guide [Bilan d'incertitude de mesure](https://houblou.github.io/metrology-lab-ai/bilan-incertitude-mesure/) présente le modèle GUM, les corrélations, la traçabilité et les limites mathématiques actuelles.

## Premiers usages

Lister les agents et construire un prompt complet prêt à copier dans les instructions d'un GPT :

```powershell
metrology-lab-ai agents
metrology-lab-ai prompt METRO-COMPARE
```

Voir le plan d'orchestration sans appeler de modèle :

```powershell
metrology-lab-ai route "Caractériser un banc de pression par comparaison avec une référence corrélée"
```

Prévisualiser le même travail avec une limite de tokens :

```powershell
metrology-lab-ai token-plan "Caractériser un banc de pression par comparaison" --mode eco
metrology-lab-ai token-plan "Caractériser un banc de pression par comparaison" --mode standard
```

Le prompt maître éditable est `src/metro_master/resources/prompts/metro-master.md`. Les plafonds sont définis dans `src/metro_master/resources/token-budget.json`. Les modes `eco`, `standard` et `deep` limitent le total estimé, la taille de chaque appel, le nombre de rôles et conservent une réserve dédiée à `METRO-AUDIT`. Voir [la documentation de gestion des tokens](docs/token-management.md).

Calculer un budget corrélé et une comparaison :

```powershell
metrology-lab-ai budget examples\budget_correlated.json --trace-out traces\budget.json
metrology-lab-ai compare examples\comparison_correlated.json
metrology-lab-ai paired examples\paired_comparison.json
metrology-lab-ai separate examples\separation_conditional.json
```

Les commandes de calcul rendent toujours l'enveloppe complète `CalculationRecord`, y compris la trace. `--trace-out` écrit séparément cette trace et refuse d'écraser un fichier existant.

Interroger le catalogue :

```powershell
metro-master library --query comparaison
metro-master library --publisher BIPM/JCGM
```

Interroger puis extraire un lot de vingt pages de la bibliothèque PDF gouvernée :

```powershell
metro-master pdf-search --query "JCGM 100 2008 FR"
metro-master pdf-extract JCGM-100-2008-FR --chunk 1
```

En orchestration Python, `MetroOrchestrator.execute_pdf_record(...)` vérifie l'empreinte, lit tous les lots successivement avec `PDF-EXTRACTOR`, réalise une synthèse paginée, puis transmet uniquement cette synthèse aux autres spécialistes et à `METRO-AUDIT`.
Voir [examples/run_with_pdf_backend.py](examples/run_with_pdf_backend.py) pour le branchement complet.

## Recherche Internet et mémoire locale

`WEB-RESEARCHER` procède en trois phases : planification, affinage des lacunes, puis synthèse. Le noyau ne contient aucune clé et n'impose aucun service. Il faut injecter un adaptateur qui implémente `ResearchProvider.search()` et retourne des `ResearchSource` structurées. Sans adaptateur, la tentative est conservée avec le statut `rejected` et n'est jamais remplacée par une recherche imaginaire.

```python
from metro_master import CallableResearchProvider, KnowledgeStore
from metro_master.orchestrator import MetroOrchestrator

def search_with_your_service(request):
    # Appeler ici le SDK ou service autorisé, lire les pages, puis retourner
    # une liste de ResearchSource ou de dictionnaires conformes au contrat.
    return []

orchestrator = MetroOrchestrator(
    research_provider=CallableResearchProvider(search_with_your_service),
    knowledge_store=KnowledgeStore("knowledge/registry"),
    max_research_rounds=3,
)
```

La mémoire n'est pas un réentraînement automatique. Elle est un registre de récupération traçable. Les nouvelles sources et inférences sont `candidate` ; seules les connaissances `validated` sont indexées et injectées automatiquement dans les études suivantes. `HybridRagRetriever` combine score lexical et similarité cosinus.

Le fournisseur intégré `HashingEmbeddingProvider` construit des vecteurs reproductibles de mots et bigrammes sans dépendance. Il apporte une vraie recherche vectorielle locale, mais pas une compréhension sémantique profonde. Pour celle-ci, branchez un modèle d'embedding avec `CallableEmbeddingProvider` et `VectorKnowledgeIndex`.

```powershell
metro-master knowledge-list
metro-master knowledge-search "comparaison pression"
metro-master knowledge-search "comparaison pression" --mode lexical --include-candidates
metro-master knowledge-promote web-source-0123456789abcdef `
  --approved-by "Responsable métrologie" `
  --reason "Source officielle lue et portée vérifiée"
metro-master knowledge-supersede web-source-0123456789abcdef `
  --approved-by "Responsable métrologie" `
  --reason "Édition remplacée"
```

Le choix et la comparaison avec l'entraînement continu ou une base vectorielle autonome sont documentés dans [l'ADR 0005](docs/adr/0005-governed-research-and-memory.md).

## Texte libre, vérification finale et historique

Pour une demande de calcul en langage naturel, le routeur ajoute `MODEL-COMPILER`. Chaque nombre, booléen et unité critique du `payload` doit être relié à une source de confiance. Le moteur refuse une valeur sans preuve, une preuve visant le mauvais champ, une sortie narrative d'agent utilisée comme source ou un extrait qui ne contient pas la valeur déclarée. Les choix de méthode et hypothèses sont acceptés seulement s'ils sont explicites et le résultat reste `conditional`.

`METRO-AUDIT` doit relier les nombres de sa conclusion aux résultats avec `conclusion_claims`. Après le dernier tour, `ConclusionVerifier` compare automatiquement identifiant, JSON Pointer, valeur et unité. Le statut devient `verified`, `failed`, `unverified` ou `not_applicable`. Ce contrôle ne prétend pas comprendre toute la conclusion en langage naturel.

Pour conserver chaque étude :

```python
from metro_master import StudyStore
from metro_master.orchestrator import MetroOrchestrator

orchestrator = MetroOrchestrator(
    study_store=StudyStore("studies/registry"),
)
result = orchestrator.execute("...", backend)
print(result.study_reference)
```

Une nouvelle exécution avec le même `study_id` ajoute une révision et ne remplace jamais l'ancienne. Commandes disponibles :

```powershell
metro-master study-list
metro-master study-show study-20261105t120000-0123456789ab
metro-master study-export study-20261105t120000-0123456789ab `
  --kind technical-report --output exports\rapport.md
metro-master study-export study-20261105t120000-0123456789ab `
  --kind draft-certificate --output exports\projet-certificat.md
metro-master study-export study-20261105t120000-0123456789ab `
  --kind accreditation-assessment --output exports\revue-accreditation.md
```

Le projet de certificat et l'aide à l'accréditation sont volontairement non officiels. Un certificat opposable ou une décision d'accréditation exige l'identité, la portée, le système qualité et la signature de l'autorité habilitée. L'architecture et les compromis sont décrits dans [l'ADR 0006](docs/adr/0006-rag-model-verification-study-ledger.md).

## Règle centrale pour la comparaison de bancs

Pour l'écart \(d=x_b-x_r\) :

\[
u^2(d)=u^2(x_b)+u^2(x_r)-2\,\operatorname{cov}(x_b,x_r)
\]

Cette relation décrit l'incertitude de l'écart. Elle n'identifie pas automatiquement l'incertitude complète du banc. La fonction et la commande `separate` refusent donc le calcul tant que l'appelant n'a pas confirmé explicitement l'identifiabilité du modèle et la connaissance de la covariance. Les composantes non observées pendant la comparaison (usage futur, reproductibilité à long terme, domaine, montage, environnement, dérive, logiciel, etc.) restent à évaluer.

Voir [docs/comparison-method.md](docs/comparison-method.md) pour la méthode complète et les pièges de double comptage.

La première ébauche importée de `expert-theorie-mesure` a fait l'objet d'une [revue structurée](docs/review-expert-theorie-mesure.md). Son verdict est **validé sous conditions** : bon socle conceptuel, mais calcul numérique laissé au noyau Python.

## ChatGPT et orchestration Python

Deux modes sont prévus :

1. **ChatGPT manuel** — créer un GPT par rôle avec le prompt composé par la commande `prompt`, ou utiliser le coordinateur dans un seul GPT. Les résultats intermédiaires sont transmis manuellement. Les GPT personnalisés ne sont jamais supposés communiquer automatiquement.
2. **Python orchestré** — `MetroOrchestrator` construit un plan, impose `METRO-AUDIT` en dernière étape, appelle un adaptateur de modèle fourni par l'utilisateur et transmet un contexte JSON entre les rôles. Un agent peut émettre des `calculation_requests` structurées : `DeterministicEngine` les valide, les exécute et joint leurs enregistrements `ok` ou `rejected` au contexte de l'auditeur.

L'exemple [examples/run_with_backend.py](examples/run_with_backend.py) montre le contrat minimal d'un adaptateur sans imposer de SDK ni de fournisseur.
L'exemple [examples/run_structured_backend.py](examples/run_structured_backend.py) montre le passage réel d'une demande structurée par le moteur. Le format complet est décrit dans [docs/structured-execution.md](docs/structured-execution.md).

## Auto-extensibilité gouvernée

`MODULE-BUILDER` peut proposer un manifeste déclaratif lorsque la capacité nécessaire n'apparaît pas dans `available_calculation_modules`. L'orchestrateur peut enregistrer automatiquement cette proposition comme `candidate` lorsqu'un `ModuleStore` lui est fourni. L'agent ne peut jamais promouvoir ou activer sa propre proposition.

Cycle CLI complet :

```powershell
metro-master module-submit modules\examples\linear-scale.json --created-by "agent:MODULE-BUILDER"
metro-master module-test linear-scale 1.0.0
metro-master module-promote linear-scale 1.0.0 --approved-by "Responsable métrologie"
metro-master module-run linear-scale modules\examples\linear-scale-input.json
metro-master module-list
```

Les expressions sont interprétées par un AST autorisé, sans `eval`, import, accès fichier ou réseau. Les unités font l'objet d'une analyse dimensionnelle conservatrice. La promotion exige au moins deux cas de référence réussis et un approbateur humain nommé. `module-deprecate` retire une version active ; `module-rollback` réactive une version validée antérieure.

Branchement dans un processus orchestré :

```python
from metro_master import DeterministicEngine, ModuleStore
from metro_master.orchestrator import MetroOrchestrator

store = ModuleStore("modules/registry")
engine = DeterministicEngine.from_store(store)
orchestrator = MetroOrchestrator(engine=engine, module_store=store)

# Après une promotion ou un rollback effectué par un humain :
orchestrator.refresh_modules()
```

## Bibliothèque documentaire

Le catalogue embarqué est dans `src/metro_master/resources/library/catalog.json`. Les fichiers légalement disponibles peuvent être déposés dans `library/documents/`, puis déclarés dans une copie locale du catalogue. Trois états probatoires sont distingués :

- `metadata_only` : titre, édition, statut et URL uniquement ;
- `excerpt_provided` : extrait précis fourni, portée limitée à cet extrait ;
- `full_text_provided` : document complet réellement disponible dans le projet.

Ne changez jamais l'état vers `excerpt_provided` ou `full_text_provided` sans fournir le fichier et son empreinte SHA-256.

Une bibliothèque externe gouvernée est également enregistrée en lecture seule dans `library/source-roots.json`. Son état, sa couverture et sa méthode de chargement contextuel sont décrits dans [docs/context-library-cnam.md](docs/context-library-cnam.md). Les copies locales y restent `local_copy_unread` tant qu'aucune extraction paginée n'a été réalisée.

Le dépôt inclut le paquet bibliographique portable dans `library/external/cnam-metrologie` : 69 notices, le manifeste des 34 PDF, leurs liens officiels et empreintes, ainsi que les guides de gouvernance et de sélection. Les PDF eux-mêmes ne sont pas versionnés lorsque leur notice limite la copie à un usage local ou interdit la redistribution. Ils peuvent être restaurés localement depuis les sources officielles ou depuis une bibliothèque autorisée, puis contrôlés contre le manifeste.

## Limites assumées

- Ce logiciel assiste une analyse ; il ne remplace ni la compétence du laboratoire, ni la validation d'une méthode, ni une revue d'accréditation.
- La transformation du texte en modèle n'est fiable que dans la mesure où les nombres, unités et hypothèses sont explicitement présents et couverts par les preuves structurées. Une ambiguïté doit produire un refus.
- Le vérificateur final contrôle les affirmations numériques déclarées et leurs unités. Il ne prouve pas automatiquement la justesse de toute conclusion scientifique en langage naturel.
- Les exports réglementés sont des projets. Le logiciel ne peut ni signer un certificat, ni accorder une accréditation.
- Le noyau implémente une propagation linéaire. Pour un modèle fortement non linéaire ou une distribution non gaussienne, utiliser une méthode adaptée (par exemple Monte-Carlo) et documenter sa validation.
- Le noyau ne fournit pas lui-même de moteur de recherche commercial ni de navigateur. La qualité, les quotas, les clés et les droits d'accès du `ResearchProvider` restent sous la responsabilité de l'intégrateur.
- L'embedding intégré est vectoriel mais lexical. Une recherche sémantique multilingue nécessite un modèle d'embedding injecté. Un corpus volumineux nécessitera également un index vectoriel spécialisé.
- L'extraction PDF repose sur la couche texte du fichier. Une page scannée ou une formule uniquement graphique est signalée comme vide ou potentiellement incomplète ; aucun OCR ni reconstruction de formule n'est improvisé.
- L'approbateur de module est actuellement une identité déclarée dans la CLI, pas une authentification cryptographique. Pour un usage multi-utilisateur, ajouter identité, signature et contrôle d'accès.
- Le langage déclaratif couvre des formules scalaires. Monte-Carlo, régression, optimisation et algorithmes itératifs exigent encore un module natif revu ou un futur worker Python isolé.
- Une matrice de corrélation doit être justifiée et positive semi-définie. La mettre à zéro « faute d'information » est une hypothèse, pas un fait.
- Les métadonnées évoluent. Vérifier l'édition et les amendements applicables avant toute décision réglementaire ou contractuelle.
- Le comptage local des tokens est une estimation indépendante du fournisseur. Une limite de sortie stricte exige que l'adaptateur LLM accepte et transmette `max_output_tokens`.

## Licence

Le code et les documents propres à MetrologyLab AI sont distribués sous [Apache License 2.0](LICENSE). Les méthodes statistiques font notamment référence au NIST/SEMATECH e-Handbook, publication du gouvernement américain ; cette mention ne constitue pas une approbation du projet par le NIST ou SEMATECH. Aucun texte intégral de norme ou contenu propriétaire n'est redistribué.

## Carte du projet

```text
src/metro_master/
  agents.py          composition des prompts
  token_budget.py    profils, estimation, réserve d'audit et registre de consommation
  orchestrator.py    routage et échanges explicites
  execution.py       contrat structuré et moteur déterministe unique
  validation.py      invariants numériques, unités et covariance
  pdf_library.py     manifeste gouverné, SHA-256 et extraction par lots
  research.py        requêtes Web, politiques de sources et adaptateur
  knowledge.py       mémoire locale, intégrité, recherche et promotion
  rag.py             embeddings, index vectoriel persistant et RAG hybride
  conclusion.py      vérification des valeurs et unités de la conclusion
  study_history.py   révisions append-only et chaîne d'intégrité
  reporting.py       rapports et projets réglementés non officiels
  module_registry.py registre versionné, AST sûr et cycle de promotion
  uncertainty.py     budgets et corrélations
  comparison.py      écarts, En, zêta, paires, séparation conditionnelle
  library.py         catalogue et contrôles de provenance
  resources/         prompts et métadonnées embarqués
docs/                architecture, méthode, ChatGPT et validation
examples/            entrées reproductibles et adaptateur
modules/             exemples et registre local de capacités extensibles
knowledge/           registre local des connaissances candidates/validées
studies/             historique persistant des études et révisions
tests/               cas nominaux, corrélés et refus sûrs
library/documents/   documents ajoutés légalement par l'utilisateur
skills/              compétence Codex portable expert-theorie-mesure
```

