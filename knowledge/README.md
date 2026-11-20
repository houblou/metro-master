# Mémoire locale

`knowledge/registry/` reçoit les enregistrements créés par `KnowledgeStore`.

- `candidate` : mémorisé avec provenance, non réutilisé automatiquement ;
- `validated` : contrôlé et promu par un humain, éligible à la recherche contextuelle ;
- `superseded` : périmé ou remplacé, exclu de la recherche.

Une source Web, un lot PDF ou une synthèse d'agent reste candidat à sa création. La présence dans ce dossier ne prouve ni l'exactitude, ni l'applicabilité, ni l'actualité du contenu.

Le sous-dossier `_vector_index/` est reconstruit automatiquement à partir des seuls enregistrements `validated`. Son empreinte, l'identifiant du fournisseur d'embeddings et les empreintes de contenu sont vérifiés avant utilisation.
