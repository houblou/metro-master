# Caractériser un banc par comparaison

## 1. Trois résultats différents

Une comparaison peut produire au moins trois objets, qu'il faut conserver séparément :

1. l'écart observé et la correction estimée ;
2. l'incertitude de l'écart ou de la correction ;
3. l'incertitude d'un futur résultat du banc, dans un domaine et des conditions définis.

Le troisième ne découle pas automatiquement du deuxième. Une séquence courte peut estimer précisément un biais moyen tout en ignorant dérive longue durée, nouveaux montages, opérateurs ou conditions d'usage.

## 2. Modèle de base et corrélation

Avec `d = x_b - x_r` :

\[
\operatorname{var}(d)=u_b^2+u_r^2-2\,\operatorname{cov}(x_b,x_r)
\]

et `cov(x_b,x_r) = rho * u_b * u_r` dans le cas scalaire. Une corrélation positive diminue l'incertitude de l'écart ; elle ne rend pas nécessairement les valeurs absolues plus sûres. Un étalon, une correction ou un environnement commun peut s'annuler dans `d`.

Registre minimal des composantes :

| Groupe | Exemples |
|---|---|
| banc | résolution, répétabilité, correction, dérive du banc |
| référence | certificat, stabilité et indication de référence |
| partagé | même étalon amont, même constante, même environnement ou logiciel |
| transfert | transport, stabilité, chargement, repositionnement de l'artefact |
| comparaison | synchronisation, interpolation temporelle, séquence, appariement |

## 3. Données appariées

Pour des paires `d_i = b_i - r_i`, calculer d'abord la moyenne des différences, `s(d)` et `s(d)/sqrt(n)`. L'appariement absorbe les effets communs variant ensemble. La dispersion de `d_i` contient déjà tout effet variant pendant la séquence ; ajouter ensuite les mêmes répétabilités comme indépendantes crée un double comptage.

Une séparation des composantes peut nécessiter des séries supplémentaires : répétitions propres à chaque banc, troisième référence, permutations d'ordre, plusieurs étalons de transfert, niveaux et campagnes temporelles.

## 4. Inversion conditionnelle

Algébriquement :

\[
u_b^2=u_d^2-u_r^2+2\,\operatorname{cov}(x_b,x_r)
\]

Mais l'opération est identifiable uniquement si :

- les trois termes portent sur le même modèle et la même période ;
- la covariance est connue ou défendue par une analyse de sensibilité ;
- `u_d` représente bien les contributions visées, sans omission ni double comptage ;
- les contributions du futur usage absentes de la comparaison sont ajoutées séparément ;
- le résultat reste physiquement admissible et non négatif.

La fonction Python exige `identifiability_confirmed=True` pour rendre ce choix visible dans le code. Ce drapeau n'est pas une preuve : le rapport doit conserver les hypothèses.

## 5. Indicateurs de compatibilité

Le score zêta travaille avec des incertitudes-types :

\[
\zeta=\frac{x_b-x_r}{u(d)}
\]

L'erreur normalisée emploie habituellement des incertitudes élargies compatibles :

\[
E_n=\frac{x_b-x_r}{\sqrt{U_b^2+U_r^2-2\rho U_bU_r}}
\]

Un indicateur satisfaisant signifie que l'écart est compatible avec les incertitudes déclarées selon le critère retenu. Il ne démontre pas que ces incertitudes sont complètes ni que le banc est caractérisé hors du domaine observé.

## 6. Protocole conseillé

1. Définir le mesurande, les niveaux, le domaine et le futur usage.
2. Cartographier les chaînes de traçabilité et les effets communs.
3. Qualifier l'étalon de transfert : stabilité, homogénéité, transport, montage.
4. Fixer avant essai la séquence, les cycles, les répétitions, la stabilisation, les critères et les métadonnées.
5. Alterner/randomiser l'ordre lorsque la dérive peut se confondre avec l'effet banc.
6. Conserver les données brutes appariées et l'environnement horodaté.
7. Ajuster la correction et diagnostiquer les résidus par niveau et temps.
8. Construire le budget par propriétaire et la matrice de covariance.
9. Réaliser une analyse de sensibilité sur les corrélations incertaines.
10. Faire une revue indépendante avant de conclure.

## 7. Cas limites

- `u_d² < u_r²` sous indépendance : ne forcez pas `u_b = 0`; l'indépendance ou les entrées sont probablement incompatibles.
- corrélation parfaite et mêmes sensibilités : l'effet commun peut s'annuler ; la matrice est semi-définie et reste admissible.
- peu de laboratoires : une moyenne/dispersion des participants peut être instable et non indépendante ; privilégier une valeur assignée traçable lorsque possible.
- modèle non linéaire : la propagation du premier ordre peut être insuffisante ; employer une méthode validée et documentée.

