# ADR 0006 — RAG vectoriel, compilation de modèles, vérification finale et registre d'études

- Statut : accepté
- Date : 2026-11-05
- Version cible : 0.6.0
- Remplace partiellement : ADR 0005 pour la stratégie de recherche locale

## Exigences

Le système doit retrouver les connaissances antérieures au-delà d'une simple recherche lexicale, transformer un texte libre en entrée de calcul sans inventer de valeurs, vérifier les nombres annoncés dans la conclusion et conserver chaque étude dans un historique auditable. Il doit également préparer les livrables d'un laboratoire sans usurper l'autorité d'un signataire ou d'un organisme d'accréditation.

Contraintes : fonctionnement hors ligne possible, aucune dépendance obligatoire, données candidates exclues du RAG actif, résultats reproductibles, détection des modifications et compatibilité avec les adaptateurs LLM existants.

## Architecture retenue

```text
texte libre ──> MODEL-COMPILER ──> preuves par champ ──> moteur déterministe
     │                                                    │
     ├──> RAG hybride <── index vectoriel <── connaissances validées
     │                                                    │
     └──────────────────── contexte ──────────────────────┘
                                                          │
                                     conclusion LLM + claims structurés
                                                          │
                                      ConclusionVerifier déterministe
                                                          │
                                      StudyStore append-only + SHA-256
                                                          │
                            rapport / projet de certificat / aide à la revue
```

### RAG

`VectorKnowledgeIndex` conserve des vecteurs normalisés avec l'empreinte du contenu et l'identifiant du fournisseur d'embeddings. `HybridRagRetriever` combine similarité cosinus et score lexical. L'index ne contient que les connaissances `validated` et se reconstruit lorsqu'un contenu, un statut ou un modèle change.

`HashingEmbeddingProvider` fournit un repli vectoriel lexical reproductible. `CallableEmbeddingProvider` permet de brancher un modèle sémantique local ou distant. Le repli n'est pas présenté comme un modèle sémantique.

### Compilation du texte

`MODEL-COMPILER` peut proposer une `CalculationRequest`, mais chaque nombre, booléen et unité doit être couvert par une preuve structurée. Le moteur vérifie le JSON Pointer, la présence de l'extrait dans une source de confiance et la correspondance de valeur. Les sources admises sont la demande, un résultat déterministe, une connaissance validée, un lot PDF identifié ou une source Web enregistrée. Une simple sortie narrative d'agent est exclue. Les hypothèses et choix méthodologiques sont déclarés et rendent la provenance `conditional`. Une donnée absente produit un refus, pas une valeur par défaut silencieuse.

### Vérification de conclusion

La conclusion finale publie des `conclusion_claims` reliés à un identifiant de calcul et à un JSON Pointer de résultat. `ConclusionVerifier` contrôle valeur et unité, détecte calcul rejeté, identifiant ambigu, résultat absent et calcul non couvert. Sa portée reste numérique. La cohérence scientifique et sémantique demeure une responsabilité humaine.

### Historique

`StudyStore` écrit des révisions immuables. Chaque révision contient l'empreinte de la précédente. Une modification, suppression intermédiaire ou permutation brise la chaîne. Aucun appel ne remplace une révision existante.

### Livrables réglementés

Le système génère un rapport technique, un projet préparatoire de certificat et une aide à la revue d'accréditation. Les deux derniers portent des avertissements non supprimables dans le générateur. L'émission officielle exige le système qualité, l'identité, la portée et la signature d'une personne ou d'un organisme habilité.

## Options écartées

- **Laisser le LLM vérifier sa propre conclusion** : non indépendant et non reproductible.
- **Accepter un modèle calculatoire sans preuves par champ** : transforme une extraction plausible en donnée supposée vraie.
- **Indexer les candidats** : risque de recycler une hallucination avant validation.
- **Émettre automatiquement un certificat ou une décision d'accréditation** : absence d'autorité, d'identité forte et de contrôle de portée.
- **Imposer un service d'embeddings** : crée une dépendance réseau, financière et de confidentialité.

## Fiabilité et échelle

L'index JSON et la recherche exhaustive conviennent à un registre local modeste. Au-delà de quelques dizaines de milliers de fragments, il faudra un moteur ANN, des lots d'embeddings, un verrou d'écriture et des sauvegardes transactionnelles. Le contrat `EmbeddingProvider` et les statuts de `KnowledgeStore` sont conservés pour cette migration.

Le registre d'études est local et mono-processus. Un déploiement partagé devra ajouter verrouillage, contrôle d'accès, journal signé, sauvegarde et horodatage de confiance.

## Points à réexaminer

- découpage et reranking sémantique des longs documents ;
- évaluation de rappel/précision sur un corpus CNAM réel ;
- ontologie d'unités et extraction de tableaux ;
- vérification sémantique assistée avec preuves contradictoires ;
- signature électronique et intégration au système qualité du laboratoire ;
- stockage SQL/objet et index vectoriel dédié à grande échelle.
