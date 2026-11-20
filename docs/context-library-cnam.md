# Bibliothèque externe « Métrologie — cours CNAM »

## Enregistrement

Racine portable enregistrée en lecture seule :

```text
library\external\cnam-metrologie
```

Le dépôt contient les 12 fichiers de catalogue, de gouvernance et de métadonnées. Les 34 PDF de la bibliothèque source ne sont pas publiés : leur manifeste impose une copie locale privée ou d'autres restrictions de reproduction. Leur emplacement logique, leurs liens officiels et leurs empreintes restent décrits dans `00 - Catalogue/manifest-pdf.csv`.

## État vérifié le 5 novembre 2026

- 46 fichiers au total, répartis dans 6 sous-dossiers ;
- 34 PDF documentés par le manifeste ;
- 69 notices au catalogue : 19 P0, 27 P1, 21 P2 et 2 P3 ;
- 34 empreintes SHA-256 concordantes, aucune absence ni divergence ;
- aucun fichier marqué hors ligne par OneDrive ;
- 30 notices indiquent un texte payant avec aperçu officiel et ne correspondent pas à un texte ISO/IEC local librement exploitable.

Dans le dépôt, le statut est `metadata_only`. Sur la machine source, la présence et l'intégrité des 34 copies locales ont été vérifiées le 5 novembre 2026, mais leur contenu n'était pas encore analysé page par page.

Depuis METRO-MASTER 0.3.0, `GovernedPdfLibrary` peut vérifier à nouveau l'empreinte, extraire la couche texte par lots de vingt pages et transmettre ces lots à `PDF-EXTRACTOR`. L'extraction ne change pas automatiquement le statut du catalogue : la synthèse doit encore être validée et enregistrée avant qu'une copie puisse être considérée comme analysée.

## Couverture locale

- **JCGM/BIPM** : GUM français/anglais, amendement 2026, Monte-Carlo, sorties multiples, conformité, GUM-1, GUM-5, GUM-6, VIM, SI, CIPM MRA comparaisons et CMC ;
- **ILAC/EA** : P9, P10, P14, G8, G17, G24, EA-4/02, EA-4/18 et EA-4/21 ;
- **EURAMET/OIML** : guide de comparaison, VIML et incertitude en métrologie légale ;
- **guides pratiques** : NIST TN 1297, NPL GPG 11, UKAS M3003 et Mari–Carbone–Petri ;
- **Cofrac** : LAB REF 02, GEN REF 10, GEN GTA 01, LAB GTA 18 et LAB GTA 22.

## Règle de chargement du contexte

Ne jamais charger les 34 PDF ensemble. Pour chaque question :

1. qualifier la décision, le mesurande et le domaine ;
2. interroger le catalogue externe et sélectionner le paquet minimal ;
3. vérifier édition, statut, priorité, droits et empreinte ;
4. extraire seulement les pages utiles avec leur pagination ;
5. distinguer texte lu, résumé interne, métadonnées et inférence ;
6. transmettre les extraits au spécialiste concerné ;
7. conserver la provenance dans le rapport et demander une validation humaine pour l'applicabilité.

## Routage documentaire conseillé

| Tâche | Paquet initial |
|---|---|
| concepts et mesurande | VIM, GUM-1, GUM-6, Brochure SI |
| budget linéaire | JCGM 100 + amendement, GUM-6 |
| modèle non linéaire | JCGM 100 + amendement, JCGM 101, GUM-6 |
| étalonnage accrédité | JCGM 100, EA-4/02, ILAC P14, ILAC P10, documents Cofrac pertinents |
| comparaison de bancs | GUM/GUM-6, EURAMET Guide 4, CIPM MRA-G-11, EA-4/21, ILAC P9 selon l'objectif |
| conformité | JCGM 106, ILAC G8 et OIML G19 si métrologie légale |
| intervalles | ILAC-G24/OIML D 10, historique et contrôles internes |

Les normes ISO/IEC payantes peuvent apparaître au catalogue comme notices applicables, mais leur texte intégral n'est pas présumé disponible. Les fiches Techniques de l'Ingénieur R140, R113, R280, R353, R560 et R603 restent également des métadonnées tant que les PDF autorisés ne sont pas fournis.

## Articulation avec le catalogue embarqué

Le catalogue inclus dans le paquet Python sert de socle portable. Pour les travaux sur cette machine, le catalogue externe gouverné devient la source de vérité documentaire pour les versions, priorités, droits et relations. Une notice n'est pas copiée automatiquement d'un catalogue à l'autre afin d'éviter deux vérités de version divergentes.

