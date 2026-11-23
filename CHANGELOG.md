# Journal des versions

Les changements importants de MetrologyLab AI sont consignés dans ce fichier. Le projet suit la numérotation sémantique. Avant la version 1.0, un changement de nom d'invocation ou d'installation augmente la version mineure.

## [0.9.0] - 2026-11-23

### Sécurisé

- seul `MODEL-COMPILER` peut désormais soumettre une requête de calcul provenant d'un agent ; les autres tentatives sont rejetées et tracées ;
- ajout d'une porte de complétude déterministe après `METRO-AUDIT` afin qu'un calcul non couvert ne termine plus comme succès silencieux ;
- chaque calcul, réussi ou rejeté, porte une trace canonique avec preuves, module, versions, empreintes et chaîne de traces ;
- les sorties CLI de calcul utilisent la même enveloppe traçable et peuvent écrire la trace avec `--trace-out`.

### Ajouté

- registre gelé des quatre sources scientifiques avec commits, blobs, licences et modes d'usage ;
- alias publics `metrology_lab_ai`, `python -m metrology_lab_ai` et `metrology-lab-ai` ;
- exécution des tests du layout `src` sans installation via `python -m unittest discover -s tests -t .`.

### Corrigé

- `CONTEXT.md` décrit maintenant `StudyStore` et la persistance réellement disponible ;
- Welch–Satterthwaite est calculé lorsque les corrélations ne touchent que des composantes à degrés de liberté infinis ;
- une corrélation impliquant une composante à degrés de liberté finis reste explicitement non calculable sans modèle conjoint validé.

## [0.8.0] - 2026-11-23

### Renommé

- le projet et son affichage public deviennent **MetrologyLab AI** ;
- le dépôt GitHub devient `houblou/metrology-lab-ai` ;
- le skill installable devient `$metrology-lab-ai` dans `skills/metrology-lab-ai` ;
- le manifeste du plugin, les instructions d'installation et les métadonnées utilisent le nouveau nom.

### Compatibilité

- le paquet Python `metro_master`, la distribution `metro-master`, la commande `metro-master`, la variable `METRO_MASTER_PROJECT_ROOT` et le rôle interne `METRO-MASTER` restent disponibles ;
- le changement de nom du skill justifie le passage de `0.7.1` à `0.8.0`.

## [0.7.1] - 2026-11-23

### Retiré

- toutes les notices, références, URL et consignes liées à des ressources couvertes par une licence personnelle dans la distribution publique ;
- toute possibilité de propager ces ressources via le catalogue, les prompts ou les compétences embarquées.

### Sécurité documentaire

- ajout d'une règle explicite maintenant les documents privés hors du dépôt public, de ses manifestes et de ses métadonnées ;
- contrôle automatisé de l'absence d'identifiants réservés dans le catalogue distribué.

## 0.7.0 - 2026-11-23

### Ajouté

- compétence Agent Skills METRO-MASTER installable et manifeste de plugin ;
- guide français de statistiques d'ingénierie inspiré du NIST/SEMATECH Handbook ;
- workflow français, piloté par l'état, pour créer, reprendre et auditer un rapport métrologique ;
- pont portable entre la compétence installée et le moteur Python ;
- notices de provenance pour les inspirations tierces ;
- commande `metro-master --version`.

### Amélioré

- routage automatique de Gauge R&R, EDA, capabilité, SPC, CUSUM, EWMA, ANOVA, DOE, régression et fiabilité vers `DATA-METRO` ;
- portes de décision statistiques et garde-fous de `DATA-METRO` ;
- documentation d'installation, tests de paquetage et validation du skill.

### Retiré

- brouillon V2 ajouté par erreur et son test documentaire ; le contenu reste récupérable dans l'historique Git au commit `c6303f7`.

## 0.6.0 - 2026-11-20

### Ajouté

- première version publique du moteur déterministe, des treize agents et du routeur ;
- budgets d'incertitude corrélés, comparaisons, statistiques appariées et séparation conditionnelle ;
- bibliothèque documentaire gouvernée, extraction PDF, recherche, mémoire RAG et historique d'études ;
- modules de calcul gouvernés, exports non officiels et tests automatisés ;
- gestion des tokens avec profils `eco`, `standard` et `deep`.

[0.9.0]: https://github.com/houblou/metrology-lab-ai/releases/tag/v0.9.0
[0.8.0]: https://github.com/houblou/metrology-lab-ai/releases/tag/v0.8.0
[0.7.1]: https://github.com/houblou/metrology-lab-ai/releases/tag/v0.7.1
