# Droits d'auteur et gouvernance documentaire

## 1. Règle générale

La présence d'un lien public ne place pas un document dans le domaine public. Cette bibliothèque stocke les **métadonnées, liens officiels et résumés originaux** ; elle ne redistribue pas les textes protégés.

## 2. Politique par éditeur

| Éditeur | Accès habituel | Politique de la bibliothèque |
|---|---|---|
| ISO/IEC | Notice et aperçu publics ; texte complet généralement payant et protégé | Stocker la notice, l'édition, le statut et le lien. Ajouter un fichier intégral uniquement si l'organisation dispose d'une licence le permettant. Ne pas l'indexer dans un service accessible hors du périmètre de la licence. |
| JCGM/BIPM | Téléchargement officiel gratuit | Conserver le lien ou une copie locale contrôlée si les conditions l'autorisent. Le téléchargement gratuit ne signifie pas domaine public ; respecter les mentions JCGM. |
| Brochure sur le SI | Publication BIPM sous CC BY 4.0 pour la version courante | Réutilisation possible avec attribution et indication des modifications. |
| ILAC | Publications officielles gratuites | Conserver les liens et vérifier la mention de droits dans chaque PDF. Ne pas modifier le document officiel. |
| EA | Publications officielles gratuites | L'anglais est la version de référence. Respecter l'interdiction de revente et les conditions de reproduction. |
| EURAMET | Guides gratuits | Ne pas revendre. La reproduction autre qu'intégrale ou par extraits peut exiger une permission selon la notice du guide. |
| OIML | Publications officielles gratuites | Conserver les liens et les métadonnées ; respecter les mentions de reproduction du document. |
| NIST | Publication publique des États-Unis, selon la notice du document | Citer l'auteur, le titre, l'édition et l'URL ; vérifier les éléments tiers éventuels. |
| NPL/UKAS | Téléchargement gratuit, droits conservés | Résumer et lier ; ne pas republier le texte intégral sans autorisation. |
| Documents internes | Selon politique de l'organisation | Classer la sensibilité, limiter les accès, conserver propriétaire, version, validation et durée de conservation. |

## 3. Ingestion dans un système RAG

Avant ingestion d'un texte intégral :

1. identifier le titulaire des droits et la licence d'accès ;
2. vérifier que l'indexation, la copie et l'extraction automatisée sont autorisées ;
3. définir le périmètre des utilisateurs et la durée de conservation ;
4. stocker la provenance et le numéro de version ;
5. exclure les exemplaires personnels ou les téléchargements sans licence institutionnelle claire ;
6. empêcher la restitution de longs passages protégés ;
7. tester la suppression et le remplacement d'une édition.

## 4. Cycle de vie

- Revue trimestrielle : lignes P0/P1, ILAC, EA, EURAMET, OIML et Cofrac.
- Revue mensuelle : projets P3 en phase 40/50 ISO et transitions d'organismes.
- À chaque nouvelle édition : conserver l'ancienne notice comme historique, marquer `remplacé`, puis évaluer l'impact sur procédures, formations et prompts.
- Empreinte recommandée pour une copie locale autorisée : SHA-256, taille, date de téléchargement et URL source.
- Un document n'est déclaré `applicable` qu'après validation par le responsable métier/qualité, pas par l'agent IA seul.

## 5. Gouvernance minimale de chaque fiche

Chaque fiche doit contenir : identifiant stable, référence, titre, organisme, édition, statut, date de vérification, URL officielle, niveau de priorité, domaine, droits, propriétaire interne, date de prochaine revue et relations `remplace/remplacé par/complète/équivalent à`.

