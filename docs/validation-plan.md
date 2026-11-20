# Plan de validation

## Niveaux

1. **Tests unitaires** : formules, signes de covariance, limites, erreurs et sérialisation.
2. **Tests de référence** : cas calculables à la main, dont corrélation nulle, positive, négative et annulation commune.
3. **Tests de refus** : matrice non positive semi-définie, incertitude négative, score à dénominateur nul, séparation non identifiable.
4. **Revue métrologique** : modèle, unité, domaine, répétabilité/reproductibilité, dérive et double comptage.
5. **Validation de bout en bout** : demande, routage, prompts, calcul JSON, audit, rapport.
6. **Validation documentaire** : racine gouvernée, empreinte PDF, lots de vingt pages, pagination, pages sans texte et synthèse finale.
7. **Validation des extensions** : schéma strict, AST interdit, analyse dimensionnelle, domaine d'entrée, cas de référence, intégrité, promotion, dépréciation et rollback.
8. **Validation recherche et mémoire** : domaines autorisés, types de source, limites de passes/résultats, déduplication, fournisseur absent, empreinte mémoire, statut candidat, promotion et remplacement.
9. **Validation RAG** : dimensions, normalisation, intégrité d'index, changement de modèle, filtrage des candidats, persistance et recherche hybride.
10. **Validation compilation** : couverture de chaque nombre, JSON Pointer, présence de l'extrait, correspondance de valeur, hypothèses déclarées et rejet sûr.
11. **Validation conclusion** : valeur, unité, pointeur, calcul inconnu/rejeté, identifiant ambigu et couverture des résultats réussis.
12. **Validation historique et exports** : append-only, chaîne SHA-256, modification détectée et avertissements non officiels.

## Critères de libération

- tous les tests automatiques passent sur Python 3.11+ ;
- deux calculs indépendants concordent aux arrondis annoncés ;
- chaque corrélation non nulle a une justification ;
- la somme des termes diagonaux et croisés reproduit la variance combinée ;
- les sources utilisées sont réellement disponibles et leurs éditions sont enregistrées ;
- aucune inférence candidate n'est injectée automatiquement comme preuve ;
- aucun nombre compilé depuis le texte n'est calculé sans preuve de champ ;
- toute valeur numérique reprise dans la conclusion est vérifiée contre le moteur ;
- chaque révision persistée conserve une chaîne d'intégrité valide ;
- chaque affirmation Web critique est reliée à une source primaire ou marquée non confirmée ;
- `METRO-AUDIT` n'a plus de défaut bloquant ;
- le responsable métrologique approuve le domaine d'emploi.

## Jeux supplémentaires à fournir par le laboratoire

- données brutes anonymisées d'une comparaison représentative ;
- certificats et CMC applicables ;
- historique de dérive et conditions d'environnement ;
- protocole de montage, séquence, stabilisation et substitutions ;
- résultat de référence calculé indépendamment ou logiciel validé.

