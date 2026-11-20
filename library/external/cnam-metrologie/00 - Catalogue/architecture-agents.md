# Architecture documentaire pour un système d'agents métrologie

## Principe

Les agents partagent `catalogue.csv`, le VIM et les règles de provenance. Chaque agent ne charge ensuite que son paquet documentaire spécialisé. Un agent coordinateur arbitre le périmètre, les conflits de sources et la validation humaine.

## Rôles proposés

| Agent | Mission | Corpus minimal | Interdictions |
|---|---|---|---|
| `METRO-MASTER` | Qualifier la demande, choisir les spécialistes, contrôler édition et provenance | VIM, SI, catalogue, guide-agent | Ne produit pas seul une conclusion normative complexe |
| `THEORIA` | Concepts, modèles, vocabulaire et cohérence du mesurande | JCGM 200, GUM-1, GUM-6, articles de théorie | Ne remplace pas les exigences d'accréditation |
| `GUM-EXPERT` | Modèles, budgets, propagation, Monte Carlo, corrélations | JCGM 100 + Amd.1, 101, 102, GUM-5, GUM-6, EA-4/02 | Ne calcule pas sans modèle, données et hypothèses explicites |
| `CAL-LAB` | Étalonnage, fonctions, certificats, intervalles | ISO/IEC 17025, ISO 28037, ISO/TS 28038, ILAC P10/P14, EA-4/02, G24/D10 | Ne confond pas étalonnage et vérification/conformité |
| `METRO-COMPARE` | Comparaisons, PT, ILC et caractérisation par transfert | ISO/IEC 17043, ISO 13528 + Amd.1, ILAC P9, EA-4/18, EA-4/21, EURAMET G4, CIPM G11 | Ne déduit pas l'incertitude complète d'un simple écart |
| `STATS-MEASURE` | Fidélité, justesse, plans et validation statistique | Série ISO 5725, ISO 21748, ISO 13528 | Ne choisit pas un test après observation sans le signaler |
| `CONFORMITY` | Règles de décision et risques | JCGM 106, ILAC G8, ISO 14253-1, OIML G19 | Ne déclare pas conforme sans règle et limites identifiées |
| `TRACE-QMS` | Traçabilité, management, équipements et preuves | ISO 10012, ISO/IEC 17025, ILAC P10, Cofrac LAB REF 02/GEN GTA 01 | Ne réduit pas la traçabilité à une suite de logos/certificats |
| `LEGAL-METROLOGY` | Métrologie légale et terminologie réglementaire | OIML V1, OIML G19, réglementation nationale applicable | Doit vérifier la réglementation en vigueur avant réponse |
| `DOC-CURATOR` | Versionnage, droits, dédoublonnage et retraits | catalogue, droits-et-gouvernance, index-local | N'ingère aucun texte protégé sans licence établie |

## Routage minimal

```text
Question reçue
  ├─ Définition/concept ───────────────> THEORIA
  ├─ Budget/incertitude ───────────────> GUM-EXPERT
  ├─ Étalonnage/intervalle ────────────> CAL-LAB + TRACE-QMS
  ├─ Comparaison de bancs/PT/ILC ─────> METRO-COMPARE + STATS-MEASURE
  ├─ Conforme/non conforme ───────────> CONFORMITY
  ├─ Métrologie légale ───────────────> LEGAL-METROLOGY
  └─ Nouvelle source/version ─────────> DOC-CURATOR
```

Toute conclusion ayant un impact qualité, contractuel, réglementaire ou d'accréditation revient à `METRO-MASTER` pour synthèse, puis à un responsable humain pour validation.

## Contrat de sortie commun

Chaque agent rend :

1. **Question reformulée et périmètre**.
2. **Hypothèses et données manquantes**.
3. **Références exactes**, statut et date de consultation.
4. **Méthode ou raisonnement**, avec formules et unités si nécessaire.
5. **Résultat et incertitude/limites**.
6. **Écart entre exigence, recommandation et choix interne**.
7. **Points nécessitant validation humaine**.

## Mémoire documentaire

- Le catalogue contient la vérité de version, pas les prompts.
- Les prompts ne doivent embarquer que les identifiants de documents et les règles de routage.
- Toute nouvelle source est d'abord placée en quarantaine documentaire, contrôlée par `DOC-CURATOR`, puis promue en P0/P1/P2.
- Une source retirée n'est pas supprimée : elle passe en historique avec relation `remplacé par`.

