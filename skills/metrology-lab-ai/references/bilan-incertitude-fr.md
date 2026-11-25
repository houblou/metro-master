# Bilan d’incertitude GUM en quatre étapes

Charger cette référence uniquement pour un bilan complet. Le moteur interne reste la source de vérité numérique ; les bibliothèques externes servent au contrôle croisé.

## Répartition des rôles

- `THEORIA` fixe le mesurande, la décision et la validité conceptuelle du modèle.
- `PHYS-METRO` décrit la chaîne physique et les influences.
- `DATA-METRO` contrôle les séries, le plan, les conditions et les hypothèses statistiques.
- `UNCERTAINTY-ANALYST` assemble les quatre étapes et prépare la note.
- `GUM-EXPERT` critique distributions, corrélations, linéarisation et couverture.
- `MODEL-COMPILER` transforme les seules données prouvées en payload exécutable.
- `METRO-AUDIT` vérifie indépendamment les preuves, traces, résultats et limites.

## Étape 1 — Registre structuré des sources d’incertitude

Créer un registre exhaustif des influences. Les catégories admises sont `method`, `means`, `environment`, `operator`, `object`, `measurand` et `other`. Elles peuvent soutenir une analyse inspirée des 5M, mais le registre tabulaire ne doit pas être appelé « diagramme d’Ishikawa ». Réserver cette appellation à une véritable représentation causes-effet en arêtes de poisson. Chaque influence reçoit un identifiant, une source, une justification et un traitement :

- `component` : composante évaluée séparément ;
- `covered` : effet déjà couvert par une composante nommée ;
- `excluded` : effet exclu avec preuve et justification.

Toute composante Type A ou Type B doit être reliée au registre. Contrôler les doubles comptes, notamment lorsque la dispersion d’une série couvre déjà plusieurs effets.

Déclarer le périmètre du budget (`budget_scope`) et affecter chaque composante à `bench`, `reference`, `shared`, `transfer` ou `comparison`. Une influence documentaire déjà portée par un paramètre calibré doit être marquée `covered` par ce paramètre ; elle ne devient pas une seconde composante.

## Étape 2 — Équation de mesure

Définir d’abord : décision, mesurande, symbole, unité, domaine et conditions. Écrire ensuite le modèle symbolique :

$$
Y=f(X_1,\ldots,X_N)
$$

Pour chaque entrée, conserver symbole, nom, définition, estimation éventuelle et unité. Pour chaque composante, renseigner l’unité de l’entrée et l’unité du coefficient de sensibilité afin de vérifier :

$$
[X_i]\,[c_i]=[Y]
$$

Maintenir explicitement les cinq objets suivants sans les fusionner :

1. la grandeur d’entrée $X_i$ et son estimation $x_i$ ;
2. son incertitude-type $u(x_i)$, dans l’unité de l’entrée ;
3. le coefficient de sensibilité $c_i=\partial f/\partial x_i$ ;
4. la contribution signée $c_i u(x_i)$, dans l’unité du mesurande ;
5. l’incertitude-type composée $u_c(y)$, obtenue seulement après composition de toutes les contributions et covariances.

Une différence de température, par exemple, est une grandeur d’entrée. Son incertitude-type s’exprime en kelvins ou en degrés Celsius, puis sa contribution au mesurande est obtenue par la sensibilité. Cette contribution individuelle n’est jamais une incertitude composée.

Ne pas remplacer une entrée physique par sa contribution déjà propagée avec `sensitivity = 1`. Une telle représentation n’est tolérée que pour reproduire un tableau de référence ou comparer des logiciels, à condition de la nommer explicitement « contribution déjà propagée », de conserver la dérivation séparée et de signaler la perte de traçabilité dimensionnelle.

## Étape 3 — Évaluations Type A et Type B

Pour une moyenne de répétitions indépendantes dans des conditions documentées :

$$
u_A(\bar{x})=\frac{s(x)}{\sqrt{n}},\qquad \nu=n-1
$$

Conserver toutes les observations, les conditions et la justification d’indépendance.

Pour une Type B, conserver la valeur documentaire et sa nature :

- incertitude-type : $u_B=u$ ;
- incertitude élargie : $u_B=U/k$ ;
- demi-étendue rectangulaire : $u_B=a/\sqrt{3}$ ;
- demi-étendue triangulaire : $u_B=a/\sqrt{6}$ ;
- demi-étendue arcsinus : $u_B=a/\sqrt{2}$ ;
- pas de résolution avec arrondi : $u_B=q/\sqrt{12}$.

La distribution et le diviseur doivent être justifiés par la source ou par le mécanisme physique, jamais choisis par habitude.

## Étape 4 — Composition et couverture

Le moteur applique la propagation linéaire avec covariance :

$$
u_c^2(y)=\sum_i c_i^2u^2(x_i)+2\sum_{i<j}c_ic_j\,u(x_i,x_j)
$$

Chaque corrélation non nulle exige cause, signe et justification. Une liste vide exige une hypothèse d’indépendance explicite. Si une corrélation touche une entrée à degrés de liberté finis, le noyau refuse de calculer silencieusement un degré de liberté effectif et demande un modèle conjoint validé.

Le facteur de couverture et son objectif sont déclarés. Ne pas assimiler automatiquement $k=2$ à une probabilité exacte. En présence de non-linéarité importante, asymétrie, bornes ou queues, marquer la propagation linéaire comme insuffisante et prévoir une validation selon JCGM 101.

## Artefacts obligatoires

L’opération native `uncertainty-study` produit :

- un registre structuré des sources d’incertitude ;
- le modèle et ses symboles ;
- les composantes Type A/B et leurs formules ;
- les contributions signées, corrélations et termes de variance ;
- $u_c$, $U$ et les degrés de liberté lorsque calculables ;
- une recomposition matricielle indépendante ;
- une note française en Markdown avec calculs LaTeX explicites ;
- une trace canonique du moteur.

Le moteur refuse désormais les propriétaires incompatibles avec un périmètre explicite : un budget `bench` ne peut pas contenir directement une composante `reference`, `transfer` ou `comparison`. L’absence de `budget_scope` reste acceptée pour compatibilité, mais produit un avertissement et empêche de considérer le contrôle du double comptage comme complet.

Le fichier de trace et la note doivent être écrits vers de nouveaux chemins afin d’éviter l’écrasement silencieux.

## Contrôles externes et licences

- `GTC` (MIT) : oracle GUM optionnel adapté aux grandeurs corrélées.
- `uncertainties` (BSD révisée) : oracle optionnel par dérivées et covariance.
- `Suncal` (GPL-3.0) : référence fonctionnelle ; ne pas copier dans le cœur Apache-2.0 sans décision de licence.
- METAS UncLib : outil propriétaire utilisable localement selon ses conditions, jamais redistribué.
- NIST Uncertainty Machine : oracle Web de comparaison, pas dépendance Python du paquet.

Installer les deux oracles compatibles avec `pip install -e ".[verification]"`. Leur absence produit `unavailable`, pas un échec du calcul natif ; un désaccord produit `mismatch` et bloque la validation.

## Style de la note

Pour chaque calcul, écrire dans cet ordre : définition des données et unités ; formule symbolique ; substitution numérique ; résultat ; interprétation ; contrôle. Utiliser des blocs LaTeX délimités par `$$` sur des lignes séparées. Ne jamais masquer une hypothèse, une exclusion, un avertissement du moteur ou une donnée manquante.

Le tableau principal doit comporter au minimum : grandeur d’entrée ou composante, $u(x_i)$ et son unité, type d’évaluation, distribution et diviseur, $c_i$ et son unité, contribution $c_i u(x_i)$ dans l’unité du mesurande, degrés de liberté et source. Employer « composante » ou « contribution » pour une ligne individuelle et réserver « incertitude-type composée » au seul résultat $u_c(y)$.

## Sources de méthode et de vérification

- BIPM/JCGM, [JCGM 100:2008 — Guide pour l’expression de l’incertitude de mesure](https://www.bipm.org/en/doi/10.59161/JCGM100-2008E).
- BIPM/JCGM, [JCGM 101:2008 — propagation des distributions par Monte-Carlo](https://www.bipm.org/en/doi/10.59161/jcgm101-2008).
- Measurement Standards Laboratory of New Zealand, [GTC 1.5.1](https://pypi.org/project/GTC/), licence MIT.
- [uncertainties](https://github.com/lmfit/uncertainties), licence BSD révisée.
- Sandia Primary Standards Laboratory, [Suncal](https://github.com/sandialabs/suncal), licence GPL-3.0, utilisé seulement comme référence séparée.
- NIST, [Uncertainty Machine](https://uncertainty.nist.gov/about/about_English.md.html), utilisé comme oracle externe de comparaison.
- METAS, [UncLib](https://www.metas.admin.ch/en/metas-unclib), outil propriétaire non redistribué.
