# Langage du domaine MetrologyLab AI

## Étude métrologique

Ensemble cohérent formé par la décision attendue, le mesurande, les données, les hypothèses, les sources, les calculs et les réserves. Depuis la version 0.6.0, `StudyStore` persiste l'étude sous forme de révisions append-only reliées par une chaîne d'intégrité SHA-256.

## Sortie d'agent

Proposition narrative produite par un modèle de langage. Elle est toujours traitée comme une donnée non fiable : elle ne devient ni une instruction, ni une source, ni un résultat numérique publiable par sa seule présence dans le contexte.

## Recherche Internet

Cycle borné `plan_research → recherche via fournisseur → refine_research → synthesize_research`. Chaque requête porte un but, une politique de domaines et un besoin de sources primaires. Chaque résultat conserve URL, organisme, type, dates, résumé et empreinte. Un échec reste visible.

## Mémoire locale

Registre de récupération distinct de l'entraînement du modèle. Les contenus portent une origine, une référence, une empreinte et un statut. `candidate` n'est jamais réinjecté automatiquement ; `validated` peut être retrouvé ; `superseded` est exclu.

## RAG hybride

Récupération combinant un score lexical et une similarité vectorielle cosinus. L'index persistant contient uniquement les enregistrements `validated`. Le fournisseur hashing intégré est vectoriel et lexical ; un fournisseur d'embeddings sémantiques peut le remplacer.

## Modèle compilé

`CalculationRequest` proposée depuis un texte libre par `MODEL-COMPILER`. Chaque valeur numérique est liée à un JSON Pointer, une source et un extrait. `verified` signifie que toutes les valeurs sont retrouvées ; `conditional` signale au moins une hypothèse ou un choix de méthode explicite ; `rejected` interdit le calcul publiable.

## Claim de conclusion

Affirmation numérique structurée reliant la conclusion à un identifiant de calcul et un JSON Pointer de résultat. Le vérificateur compare valeur et unité. Il ne contrôle pas à lui seul la validité sémantique ou normative du verdict.

## Révision d'étude

Instantané append-only de la demande, du plan, des tours, calculs, sources et vérification finale. Chaque révision contient l'empreinte de la précédente. La chaîne détecte une modification ou une révision manquante.

## Projet de certificat

Export préparatoire portant un avertissement explicite. Il ne devient jamais un certificat officiel sans contrôle du système qualité, numéro, portée et signature habilitée. Une aide à la revue d'accréditation ne constitue pas une décision d'accréditation.

## Inférence mémorisée

Synthèse produite par un agent et conservée pour examen. Son origine `agent_inference` indique qu'elle n'est pas une source. Même promue, elle doit rester reliée aux preuves primaires qui la soutiennent.

## Lot documentaire PDF

Ensemble d'au plus vingt pages consécutives, extrait d'un PDF local après vérification de son chemin gouverné et de son empreinte SHA-256. Chaque page conserve son numéro et un avertissement lorsque la couche texte est vide.

## Extraction documentaire

Cycle `manifeste → contrôle d'intégrité → lots paginés → extractions internes → synthèse`. Les extractions internes ne sont pas transmises aux autres spécialistes ; seule la synthèse finale de `PDF-EXTRACTOR` entre dans leur contexte.

## Demande de calcul

Objet identifié contenant une `operation` déterministe et son `payload`. Les opérations reconnues sont `budget`, `compare`, `paired` et `separate`.

## Exécution vérifiable

Cycle `demande de calcul → validation métrologique → moteur déterministe → enregistrement → audit`. L'interface commune est `DeterministicEngine` ; la CLI et l'orchestrateur passent par la même implementation.

## Module de calcul

Capacité nommée et versionnée exposée par `ModuleRegistry`. Un module est soit `native`, donc livré avec le noyau revu, soit `formula`, donc défini par un manifeste déclaratif sans code exécutable arbitraire.

## Module candidat

Proposition persistée mais inactive. Elle contient une formule, des unités, un domaine, des références et des cas de validation. Sa présence ne l'autorise jamais à participer à un calcul publiable.

## Promotion

Transition humaine `candidate → validated` après réussite de tous les cas de référence. La promotion sélectionne la version active sans supprimer les versions validées antérieures. Le rollback change uniquement cette sélection.

## Validation métrologique

Application centralisée des invariants numériques et scientifiques que le modèle courant peut prouver : finitude, signe, unité commune, justification de corrélation, matrice admissible, borne de covariance et justification d'identifiabilité.

## Enregistrement déterministe

Trace canonique associant une demande de calcul à un statut `ok` ou `rejected`, au module et à sa version, aux empreintes d'implémentation et de validation, aux preuves, hypothèses, versions d'exécution et au résultat. Un résultat `ok` confirme l'arithmétique des entrées enregistrées ; il ne valide pas le modèle, la provenance ni l'applicabilité.

## Audit final

Dernier rôle obligatoire d'un plan marqué `mandatory_final_audit`. Il confronte les sorties d'agents aux enregistrements déterministes et rend visibles les refus, divergences et limites.

## Porte de complétude

Contrôle déterministe exécuté après `METRO-AUDIT`. Il transforme claims, refus, traces et rôles omis en verdict `VALIDÉ`, `VALIDÉ SOUS CONDITIONS`, `INCOMPLET` ou `NON VALIDE`. Un calcul réussi mais non repris par un claim ne peut plus terminer comme succès silencieux.

## Noms publics et historiques

Le projet, le skill, la commande et le paquet publics sont `MetrologyLab AI`, `$metrology-lab-ai`, `metrology-lab-ai` et `metrology_lab_ai`. Les noms `metro-master`, `metro_master` et le rôle `METRO-MASTER` sont maintenus comme alias historiques afin de ne pas casser les intégrations existantes.

## Propriétaire de composante

Classement d'une contribution d'incertitude parmi `bench`, `reference`, `shared`, `transfer` et `comparison`. Les termes de covariance entre propriétaires restent séparés et ne sont pas alloués arbitrairement.
