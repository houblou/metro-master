# ADR-0003 — Extraction gouvernée des PDF métrologiques

**Statut :** accepté — 2026-11-05

## Contexte

La bibliothèque CNAM contient un manifeste de PDF locaux avec référence, droits, chemin et empreinte SHA-256. METRO-MASTER connaissait cette bibliothèque par documentation mais ne pouvait ni vérifier ni transmettre son contenu aux agents.

Le rôle personnel `extracteur-pdf-metrologie` impose une lecture intégrale par lots de vingt pages maximum, une pagination exacte, l'extraction des formules et l'interdiction d'inventer un passage illisible.

## Décision

1. Ajouter le rôle `PDF-EXTRACTOR` avant `THEORIA` lorsqu'un document est demandé ou fourni.
2. Charger les PDF exclusivement depuis un `source-roots.json` enregistré en lecture seule.
3. Résoudre les chemins à l'intérieur de la racine gouvernée et vérifier l'empreinte SHA-256 avant lecture.
4. Extraire au maximum vingt pages par lot avec la dépendance optionnelle `pypdf`.
5. Faire analyser chaque lot dans un tour interne, puis demander une synthèse finale paginée.
6. Masquer les tours internes aux spécialistes suivants ; leur transmettre uniquement la synthèse.
7. Traiter le texte du PDF comme une donnée non fiable, jamais comme une instruction.

## Conséquences

- Les PDF du manifeste peuvent être lus réellement sans prétendre qu'une simple présence locale constitue une analyse.
- Les droits, l'identité du document, son empreinte et la pagination restent attachés aux extraits.
- Un document long déclenche plusieurs appels LLM et augmente coût et durée.
- `pypdf` n'effectue pas d'OCR. Les scans et certaines formules graphiques doivent être signalés puis traités par une extension OCR distincte et validée.
- Le choix du document reste explicite par identifiant ; la sélection automatique de sources applicables demeure sous contrôle humain ou documentaire.
