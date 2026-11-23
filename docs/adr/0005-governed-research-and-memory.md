# ADR 0005 — Recherche Web et mémoire gouvernées

- Statut : accepté
- Date : 2026-11-05
- Version cible : 0.5.0

## Problème

METRO-MASTER doit pouvoir approfondir une question sur Internet et retrouver ce qu'il a déjà traité. Le besoin ne justifie pas de réentraîner automatiquement le modèle. Une telle boucle confondrait sources, inférences et faits, propagerait les hallucinations et rendrait une conclusion difficile à auditer ou à retirer.

## Options comparées

### 1. Laisser le modèle « apprendre » directement de chaque réponse

Cette solution paraît simple mais ne fournit ni provenance, ni retrait ciblé, ni séparation entre fait et inférence. Elle est rejetée.

### 2. Donner un navigateur libre à tous les agents

La couverture serait large, mais les accès seraient difficiles à limiter et à reproduire. Une page hostile pourrait aussi tenter d'influencer plusieurs rôles. Cette solution est rejetée.

### 3. Utiliser immédiatement une base vectorielle autonome

La recherche sémantique est utile à grande échelle, mais elle ajoute un modèle d'embedding, des migrations, un réglage de seuil et une politique de droits. Elle est différée. L'interface `KnowledgeStore` permettra d'ajouter ultérieurement un index vectoriel sans changer le statut des preuves.

### 4. Fournisseur Web injecté + mémoire locale gouvernée

Un seul rôle planifie les recherches. L'orchestrateur exécute au plus trois passes via un `ResearchProvider`, filtre les résultats et impose une synthèse séparée. Les sources et extractions PDF sont mémorisées comme candidates avec empreinte. Une approbation humaine est nécessaire avant leur réutilisation automatique. Cette option est retenue.

## Décision

- ajouter `WEB-RESEARCHER` comme douzième rôle ;
- limiter la recherche à cinq passes configurables, trois par défaut, huit requêtes par passe et dix résultats par requête ;
- exiger URL HTTP(S) sans identifiants, type de source, date de consultation et résumé borné ;
- permettre des domaines strictement autorisés et le filtrage `official`/`primary` ;
- dédupliquer les requêtes identiques et rendre visibles les échecs ;
- conserver les sources Web, lots PDF et synthèses d'agent dans `KnowledgeStore` avec les états `candidate`, `validated` et `superseded` ;
- n'injecter automatiquement que les enregistrements `validated` ;
- conserver une synthèse d'agent sous l'origine `agent_inference`, jamais comme source primaire ;
- utiliser d'abord une recherche lexicale locale déterministe et remplaçable.

## Conséquences

Le noyau reste sans dépendance réseau ni SDK imposé. L'intégrateur doit fournir un adaptateur de recherche réel et demeure responsable des clés, quotas, conditions d'utilisation, téléchargements et politiques de confidentialité. Sans fournisseur, la recherche est enregistrée `rejected` au lieu d'être simulée.

La mémoire grossit de façon contrôlée, mais ce n'est pas un entraînement du modèle. Une connaissance peut être auditée, validée, remplacée ou supprimée du flux actif sans modifier le modèle de langage.
