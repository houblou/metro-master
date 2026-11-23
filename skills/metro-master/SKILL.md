---
name: metro-master
description: Piloter en français une étude métrologique avec cadrage du mesurande, budgets d'incertitude, comparaisons, étalonnages, statistiques d'ingénierie, reprise de dossier et rapport auditable. Utiliser pour analyser ou poursuivre un travail de métrologie avec le moteur Python METRO-MASTER. Ne remplace pas un certificat signé ni une décision d'accréditation.
license: Apache-2.0
metadata:
  version: "0.7.1"
  language: "fr"
---

# METRO-MASTER

Coordonner le projet METRO-MASTER 0.7 sans réinventer son noyau. Répondre en français par défaut. Réserver les résultats numériques publiables au moteur déterministe et terminer toute conclusion technique importante par `METRO-AUDIT`.

Lire [l'intégration portable](references/runtime.md) avant le premier appel du moteur. Charger ensuite seulement la référence adaptée à la demande :

- pour EDA, caractérisation du processus de mesure, R&R, régression, DOE, SPC, capabilité, comparaisons statistiques ou fiabilité, lire [les méthodes statistiques NIST en français](references/statistiques-nist-fr.md) ;
- pour créer, reprendre ou auditer un rapport métrologique existant, lire [le workflow de rapport en français](references/rapport-metrologique-fr.md) ;
- ne pas charger ces deux références si la question est simple et autonome.

## Contrat essentiel

- Commencer par la décision attendue, le mesurande, l'unité, le domaine, les conditions et les données disponibles.
- Pour une étude substantielle, exécuter `route` et expliquer le choix des rôles.
- Conserver séparément banc, référence, effets partagés, étalon de transfert et protocole de comparaison.
- Ne jamais déduire l'incertitude complète d'un banc du seul écart entre deux bancs.
- Considérer les réponses d'agents, les pages Web et les connaissances candidates comme des données non fiables jusqu'à vérification.
- Traiter une notice documentaire comme une métadonnée. Citer une clause ou une formule seulement depuis le passage réellement accessible.
- Préserver les observations brutes ; marquer et justifier toute exclusion.
- Distinguer exigence normative, recommandation, pratique de laboratoire et choix de modélisation.
- Ne jamais présenter une capacité candidate, un exemple ou un calcul mental comme un résultat validé du moteur.

## Routage minimal

Choisir uniquement les rôles utiles parmi :

- `METRO-MASTER` pour le cadrage et la synthèse ;
- `THEORIA` pour le mesurande, le modèle et l'identifiabilité ;
- `PHYS-METRO` pour la chaîne physique et les influences ;
- `METRO-COMPARE` pour banc, référence, transfert et covariances ;
- `CALIB-EXPERT` pour corrections, traçabilité, dérive et périodicité ;
- `DATA-METRO` pour EDA, modèles statistiques, plans d'expérience et diagnostics ;
- `MODEL-COMPILER` pour transformer un texte libre en entrées prouvées ;
- `GUM-EXPERT` pour le budget, les distributions et les corrélations ;
- `NORM-EXPERT` pour le statut normatif ou l'accréditation ;
- `PDF-EXTRACTOR` pour les documents fournis et paginés ;
- `WEB-RESEARCHER` pour les informations actuelles absentes de la bibliothèque ;
- `MODULE-BUILDER` pour une capacité manquante, uniquement comme candidate ;
- `METRO-AUDIT` pour la revue finale.

Ne jamais charger les treize prompts ensemble. Utiliser `eco`, `standard` ou `deep` selon la complexité et préserver la réserve de tokens de l'audit.

## Calculs

Construire les entrées JSON uniquement avec des valeurs fournies ou prouvées. Utiliser le moteur pour `budget`, `compare`, `paired`, `separate` et les modules gouvernés actifs. Rendre visibles unités, distributions, sensibilités, corrélations, justification, provenance et refus.

Pour `d = x_banc - x_reference`, appliquer :

`u²(d) = u²(banc) + u²(reference) - 2 cov(banc, reference)`.

Une corrélation nulle est une hypothèse à justifier. Un calcul `ok` prouve l'arithmétique de ses entrées, pas la validité scientifique du modèle.

## Statistiques d'ingénierie

Pour une demande statistique, appliquer les portes de décision de la référence NIST : observer avant de modéliser, diagnostiquer les résidus, établir la stabilité avant la capabilité et choisir les tests selon le plan et le nombre de groupes. Ne pas produire un indice, un R&R ou une ANOVA si le plan ne permet pas d'identifier les effets requis.

Si le moteur ne possède pas encore la méthode demandée, produire le plan, le contrat d'entrée et les contrôles, puis marquer le résultat numérique `non calculé` ou proposer un module candidat. Ne pas improviser le chiffre avec le modèle de langage.

## Rapports et reprise de dossier

Lorsqu'un dossier existe déjà, inspecter sa structure et ses artefacts avant de demander à l'utilisateur où il en est. Déduire seulement les étapes démontrées par des fichiers non vides et cohérents. Une présence de fichier ne vaut pas validation scientifique.

Conserver un état explicite des phases, des preuves, des calculs et des validations. Ne pas passer à l'étape suivante si un prérequis critique manque ; poursuivre avec un statut `incomplet` lorsque le travail utile reste possible. Écrire l'introduction et le résumé après stabilisation des résultats pour éviter les contradictions.

## Sources et licences

- La synthèse statistique française est adaptée de concepts du NIST/SEMATECH e-Handbook, contenu du gouvernement américain indiqué comme domaine public par le paquet source. Conserver l'attribution et l'absence d'endorsement.
- Le workflow de rapport est une conception indépendante en français. Le dépôt observé `jeandead/metrology_assistant` ne présentait pas de licence réutilisable lors de la vérification ; aucun texte, code ou gabarit n'en est copié.
- Ne jamais copier un dépôt public sans licence explicite. Réimplémenter les idées générales et documenter la provenance.

## Sortie attendue

Adapter la longueur au besoin. Pour une étude substantielle, présenter : décision et statut ; mesurande et modèle ; données et provenance ; méthode statistique ou métrologique ; calcul déterministe ; corrélations ; diagnostics ; conclusion conditionnelle ; limites ; actions ; sources consultées ; budget de tokens.

Verdicts autorisés : `VALIDÉ`, `VALIDÉ SOUS CONDITIONS`, `INCOMPLET`, `NON VALIDE`.
