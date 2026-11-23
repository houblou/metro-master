# Statistiques d'ingénierie inspirées du NIST — guide français

## Provenance et statut

Cette référence est une adaptation française orientée MetrologyLab AI des concepts du **NIST/SEMATECH e-Handbook of Statistical Methods, NIST Handbook 151**. Le paquet consulté indique que le contenu NIST est une œuvre du gouvernement des États-Unis dans le domaine public américain. Cette adaptation n'est pas une publication du NIST ou de SEMATECH et n'est approuvée par aucun de ces organismes.

Source consultée le 22 novembre 2026 :

- `jgsystemsconsulting/jgs-se-knowledge-packs`, `packs/nist-stat-handbook/SKILL.md` ;
- licence du paquet : `packs/nist-stat-handbook/LICENSE` ;
- source officielle à privilégier pour une citation scientifique : NIST/SEMATECH e-Handbook.

Le présent guide ne reproduit ni galeries de formules, ni jeux de données, ni figures, ni cas détaillés, ni code du Handbook. Il synthétise des critères de sélection et des garde-fous en français.

## Quand charger cette référence

La charger seulement pour :

- exploration et diagnostic de données ;
- caractérisation d'un processus de mesure ;
- biais, fidélité, stabilité ou Gauge R&R ;
- régression et étalonnage statistique ;
- plan d'expérience ;
- cartes de contrôle, capabilité ou échantillonnage d'acceptation ;
- comparaison de groupes, ANOVA ou intervalles ;
- fiabilité et essais accélérés.

Ne pas la charger pour un calcul GUM simple déjà couvert par le moteur ni pour une question documentaire sans données.

## Routeur statistique

| Question | Porte d'entrée | Contrôles indispensables |
|---|---|---|
| Les données sont-elles exploitables ? | EDA et 4 graphiques | ordre, dérive, autocorrélation, forme |
| Le système de mesure est-il bon ? | caractérisation mesure | biais, court terme, long terme, stabilité |
| Les opérateurs ou répétitions contribuent-ils ? | Gauge R&R | plan identifiable, interaction, résolution |
| Le procédé est-il capable ? | SPC puis capabilité | stabilité avant Cp/Cpk ou Pp/Ppk |
| Quelle relation relie X à Y ? | régression | résidus, variance, forme fonctionnelle |
| Quels facteurs agissent ? | DOE | randomisation, interactions, confusion |
| Une dérive est-elle détectable ? | Shewhart/CUSUM/EWMA | phase I/II, ARL, plan d'action |
| Deux ou plusieurs groupes diffèrent-ils ? | test + intervalle | appariement, nombre de groupes, hypothèses |
| Combien de temps le produit dure-t-il ? | fiabilité | réparable/non réparable, censure, modèle |

## 1. Observer avant de modéliser

Avant un test, une régression ou un indice, examiner les données dans leur ordre d'acquisition. Le diagnostic minimal combine :

1. graphique de séquence pour niveau, dérive et ruptures ;
2. graphique retardé pour dépendance et autocorrélation ;
3. histogramme ou estimation de forme ;
4. graphique de probabilité adapté à la loi supposée.

Tester quatre propriétés : position stable, dispersion stable, indépendance temporelle et distribution stable. Un échec n'est pas un simple défaut statistique : rechercher la cause physique, instrumentale, environnementale ou opérateur.

Les résidus sont le diagnostic commun à toutes les familles de modèles. Un modèle adéquat ne doit pas laisser de structure exploitable dans ses résidus.

## 2. Caractériser un processus de mesure

Séparer au minimum :

- biais par rapport à une référence ;
- dispersion de répétabilité à court terme ;
- variabilité entre jours, séries ou configurations ;
- reproductibilité entre opérateurs, montages ou laboratoires ;
- résolution, hystérésis, dérive et stabilité ;
- incertitude du résultat de mesure.

Une série répétée sur un étalon de contrôle stable permet de surveiller le processus de mesure. Utiliser une carte adaptée aux petites séries et examiner séparément dérive et dispersion. Un instrument très fidèle à court terme peut présenter une variabilité à long terme dominante.

### Gauge R&R

Exiger un plan permettant d'identifier les effets : pièces ou niveaux représentatifs, opérateurs, répétitions, ordre contrôlé ou randomisé et résolution suffisante. Ne pas calculer un R&R complet depuis une simple série répétée par un seul opérateur.

Rendre visibles : répétabilité, reproductibilité, interaction éventuelle, variation entre objets, stabilité et domaine couvert. Ne pas confondre la variation des objets avec l'erreur du système de mesure.

### Plans d'étalonnage

Pour un étalonnage par intercomparaison, identifier la contrainte de référence, l'ordre des comparaisons et les effets de position ou de dérive que le plan peut annuler. Utiliser un ajustement déterministe ou un module statistique validé ; le modèle de langage ne résout pas numériquement le système.

## 3. Stabilité avant capabilité

Un indice de capabilité sur un procédé instable ne permet pas de prédire correctement la production future. Procéder dans cet ordre :

1. définir la grandeur, le procédé, les sous-groupes et les limites de spécification ;
2. vérifier le système de mesure ;
3. établir la stabilité statistique ;
4. examiner la distribution ou choisir une méthode robuste ;
5. calculer et interpréter Cp/Cpk ou Pp/Ppk ;
6. limiter la conclusion au domaine et à la période réellement observés.

Ne jamais confondre limites de contrôle, issues du procédé, et limites de spécification, issues du besoin ou du contrat.

## 4. Modélisation et régression

Le cadre général est `y = f(x; beta) + epsilon`. Choisir :

- moindres carrés linéaires pour une forme linéaire et une variance compatible ;
- moindres carrés pondérés lorsque la variance varie de façon justifiée ;
- régression non linéaire pour une forme physique non linéaire ;
- lissage local pour explorer une forme sans imposer trop tôt un modèle global.

Vérifier : ordre et indépendance des erreurs, moyenne résiduelle, variance, distribution lorsque l'inférence l'exige, forme fonctionnelle, points influents et domaine de prédiction. Distinguer intervalle de confiance sur la moyenne et intervalle de prédiction d'une nouvelle observation.

## 5. Plans d'expérience séquentiels

Préciser l'objectif : comparaison, criblage, surface de réponse ou estimation d'un modèle. Préférer une stratégie progressive :

1. cribler les facteurs ;
2. chercher une courbure ;
3. lever les confusions importantes ;
4. concentrer les essais près de la zone utile ;
5. réaliser des essais de confirmation.

Randomiser lorsque c'est possible, bloquer les nuisances connues et conserver l'ordre réel. Une démarche un-facteur-à-la-fois masque les interactions et n'est pas le choix par défaut.

## 6. Surveillance statistique

- Shewhart : changements relativement grands et diagnostic direct ;
- CUSUM : petits décalages persistants ;
- EWMA : petites dérives avec mémoire réglable ;
- cartes d'attributs : comptes ou proportions ;
- méthodes multivariées : variables corrélées, avec modèle adapté.

Séparer la phase I, construction et nettoyage justifié des limites, de la phase II, surveillance des nouvelles données. Définir à l'avance le plan d'action hors contrôle. Une règle de détection plus sensible augmente aussi les fausses alertes ; documenter ce compromis.

## 7. Comparer correctement

Choisir selon le plan et le nombre de groupes :

- un groupe : estimation ou test par rapport à une valeur ;
- deux groupes indépendants : comparaison indépendante adaptée ;
- deux séries appariées : analyser les différences par paire ;
- trois groupes ou plus : ANOVA ou méthode robuste, puis comparaisons multiples contrôlées ;
- petits effectifs ou données discrètes : méthode exacte lorsque nécessaire.

Associer test et intervalle de confiance compatibles. « Ne pas rejeter » n'est pas prouver l'égalité. Pour une équivalence, définir une marge d'équivalence et employer une méthode dédiée.

## 8. Fiabilité

Commencer par distinguer :

- système non réparable : distribution des durées de vie et censure ;
- système réparable : processus de réparations et évolution du taux d'événements.

Le nombre de défaillances, le mécanisme de censure et la justification physique du modèle déterminent l'information disponible. Un essai accéléré exige une relation d'accélération justifiée et un domaine où le mécanisme de défaillance reste le même.

Ne pas appliquer automatiquement une loi de Weibull, lognormale ou exponentielle. Comparer diagnostics, mécanisme et sensibilité de la décision.

## Garde-fous MetrologyLab AI

- Les méthodes ci-dessus ne deviennent pas des calculs autorisés par leur seule présence dans cette référence.
- Utiliser le moteur pour les modules actifs. Sinon produire un plan, un schéma d'entrée et une proposition candidate.
- Pour GUM, conserver les règles plus strictes de MetrologyLab AI sur les corrélations, les unités et le facteur d'élargissement.
- Une carte stable ne prouve pas la conformité ; un indice de capabilité ne prouve pas la stabilité ; une différence significative ne prouve pas l'importance pratique.
- Citer la source officielle si une formule ou une condition précise soutient la conclusion.

## Livrable statistique

Présenter : question décisionnelle ; plan de données ; diagnostic EDA ; méthode et hypothèses ; calcul déterministe ; diagnostics de résidus ou stabilité ; taille d'effet et intervalle ; conclusion limitée ; données manquantes ; sources.
