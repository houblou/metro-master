# Caractériser un banc par comparaison

## 1. Principe directeur

Une comparaison répond à la question : **les résultats de deux chaînes de mesure sont-ils compatibles, pour un mesurande et des conditions définis ?** Elle ne fournit pas, à elle seule, l'incertitude complète du banc évalué.

Avant tout calcul, classer l'objectif :

1. **Étalonnage/transfert** : établir une correction ou une fonction d'étalonnage à partir d'une référence.
2. **Validation de méthode ou de banc** : démontrer l'aptitude pour un domaine d'emploi.
3. **Caractérisation de performance** : quantifier biais, répétabilité, reproductibilité, linéarité, hystérésis, dérive, stabilité et influences.
4. **Comparaison interlaboratoires/essai d'aptitude** : évaluer la comparabilité ou la performance d'un participant.

Ces objectifs peuvent partager un plan d'expérience, mais leurs modèles, critères et conclusions ne sont pas interchangeables.

## 2. Typologie à déclarer

| Dimension | Options | Conséquence principale |
|---|---|---|
| Relation | directe / indirecte par étalon de transfert | Une comparaison indirecte ajoute stabilité, transport, raccordement et parfois corrélation. |
| Temps | simultanée / alternée / successive | Le mode successif exige de traiter la dérive de la source et de l'étalon. |
| Référence | valeur certifiée / banc de référence / valeur de comparaison | Le mode d'assignation de la référence conditionne son incertitude et les corrélations. |
| Organisation | bilatérale / multilatérale / essai d'aptitude | Les statistiques et critères applicables changent. |
| But | correction / validation / surveillance / diagnostic | Le critère d'acceptation doit être fixé avant les mesures. |

## 3. Définir le mesurande et le domaine

La définition doit inclure :

- grandeur, unité, plage et points critiques ;
- objet ou signal mesuré, géométrie, montage et orientation ;
- méthode, temps d'intégration, filtrage, résolution et logiciel ;
- température, humidité, pression, vibrations, alimentation et autres influences ;
- état initial, préconditionnement, temps de chauffe et séquence ;
- propriété attribuée au résultat : instantanée, moyenne, valeur corrigée, indication brute, etc.

Un changement de montage, d'algorithme ou de condition d'influence peut constituer un autre mesurande.

## 4. Modèle de comparaison

Pour le point `i`, un modèle minimal est :

```text
d_i = (y_B,i + c_B,i) − (y_R,i + c_R,i) + δ_transfert,i + δ_temps,i + δ_env,i
```

où `B` désigne le banc évalué, `R` la référence et les `δ` les effets non déjà inclus dans les résultats corrigés.

L'incertitude-type de l'écart s'écrit, sous forme générique :

```text
u²(d_i) = u²(y_B,i) + u²(y_R,i) − 2 cov(y_B,i, y_R,i)
          + u²(δ_transfert,i) + u²(δ_temps,i) + u²(δ_env,i) + …
```

La covariance ne doit pas être posée à zéro par défaut. Elle est plausible si les deux bancs partagent un étalon, un certificat, une correction, une constante, un modèle, une acquisition ou une chaîne de traçabilité.

### Écart normalisé

Si les incertitudes élargies `U_B` et `U_R` sont exprimées avec une couverture compatible et sont indépendantes, l'indicateur usuel est :

```text
E_n = (x_B − x_R) / √(U_B² + U_R²)
```

Une valeur `|E_n| ≤ 1` indique une compatibilité selon ce modèle. Si les résultats sont corrélés, le dénominateur doit être établi à partir de l'incertitude de l'écart, covariance comprise. `E_n` est un indicateur de compatibilité/performance ; il ne démontre ni l'absence de biais ni la complétude du budget du banc.

## 5. Plan expérimental recommandé

### Points et répétitions

- Couvrir bas, milieu, haut de plage et points de décision ou de changement de gamme.
- Prévoir assez de répétitions pour estimer la répétabilité sans confondre résolution et dispersion.
- Répéter sur plusieurs jours, opérateurs ou remises en route pour l'imprécision intermédiaire.
- Mesurer en montée et en descente si une hystérésis est possible.

### Séquence

- Préférer une mesure simultanée si les deux bancs peuvent observer réellement le même mesurande sans interaction.
- Sinon utiliser une alternance de type `R–B–B–R` ou `R–B–R` et modéliser la dérive entre encadrements.
- Randomiser ou bloquer l'ordre lorsque le temps, la température ou l'usure peut biaiser les résultats.
- En circulation d'un étalon de transfert, contrôler sa stabilité avant, pendant et après, ainsi que les effets transport/choc/orientation.

### Données minimales à enregistrer

```text
run_id;date_heure;point_nominal;valeur_ref;valeur_banc;corrections;
incertitudes;covariances;température;humidité;opérateur;montage;
logiciel_version;séquence;observations;statut_validité
```

## 6. Caractéristiques à séparer

| Caractéristique | Estimation possible | Vigilance |
|---|---|---|
| Répétabilité | dispersion dans des conditions répétables | Ne couvre pas jours, opérateurs, démontages. |
| Imprécision intermédiaire | effets jour/opérateur/remontage | Plan équilibré ou modèle adapté requis. |
| Biais/correction | moyenne des écarts à une référence | La référence et sa traçabilité doivent être explicites. |
| Linéarité | résidus d'une fonction sur la plage | Employer ISO 28037:2026 ou ISO/TS 28038:2018 selon le modèle. |
| Hystérésis | différence montée/descente | Garder les mêmes conditions et temps de stabilisation. |
| Résolution | quantification/lecture | Une résolution fine ne garantit pas une faible incertitude. |
| Dérive/stabilité | évolution temporelle | Distinguer dérive source, transfert, référence et banc. |
| Robustesse environnementale | sensibilité aux grandeurs d'influence | Éviter d'extrapoler hors du domaine étudié. |
| Reproductibilité | changement de laboratoire ou de système | Ne pas la confondre avec la répétabilité. |

## 7. Analyse et décision

1. Vérifier l'intégrité, les unités, les corrections et la traçabilité.
2. Visualiser écarts et résidus en fonction du point, du temps, de la direction et des influences.
3. Tester l'adéquation du modèle ; ne pas forcer une droite si les résidus révèlent une structure.
4. Estimer les paramètres avec la méthode cohérente avec les incertitudes en `x`, en `y` et leurs covariances.
5. Construire le budget de l'écart puis, séparément, le budget du banc pour son usage cible.
6. Comparer aux critères préétablis : compatibilité, erreur maximale, capabilité ou règle de décision.
7. Documenter les écarts, exclusions, données aberrantes et analyses de sensibilité.
8. Limiter la conclusion au domaine réellement couvert.

## 8. Portes de décision

Le banc n'est déclaré apte que si :

- le mesurande et la plage d'emploi sont définis ;
- la traçabilité de la référence est démontrée ;
- le modèle et ses résidus sont acceptables ;
- les effets de temps, environnement et transfert sont maîtrisés ;
- les corrélations importantes sont traitées ;
- le budget d'incertitude d'usage est complet et séparé du seul test de compatibilité ;
- le critère d'acceptation et la règle de décision étaient définis avant la conclusion ;
- les versions de logiciel, matériel et procédure sont figées.

## 9. Signaux d'alerte

- Déduire `U_B = √(U_diff² − U_R²)` sans modèle, indépendance démontrée et composantes complètes.
- Utiliser seulement un point ou une seule répétition.
- Comparer des résultats qui ne représentent pas le même mesurande.
- Oublier la dérive d'un étalon de transfert ou la covariance issue d'une référence commune.
- Employer `E_n` avec des facteurs de couverture incompatibles.
- Retirer des valeurs comme « aberrantes » après observation sans règle documentée.
- Conclure sur toute la plage à partir d'une zone limitée.
- Confondre tolérance produit, erreur maximale tolérée du moyen et incertitude de mesure.

## 10. Corpus normatif associé

- Modèle et incertitude : JCGM 100:2008 + Amd 1:2026, JCGM GUM-6:2020, JCGM 101:2008.
- Fonction d'étalonnage : ISO 28037:2026, ISO/TS 28038:2018, ISO 11095:1996.
- Fidélité et justesse : série ISO 5725 et ISO 21748:2017.
- Compétence et traçabilité : ISO/IEC 17025:2017, ILAC P10:07/2020, EA-4/02 M:2022.
- Comparaisons : EURAMET Guide No. 4 v2.0, CIPM MRA-G-11 v1.2.
- Essais d'aptitude/ILC : ISO/IEC 17043:2023, ISO 13528:2022 + Amd 1:2026, ILAC P9:01/2024, EA-4/21 INF:2026.
- Conformité : JCGM 106:2012, ILAC G8:09/2019, ISO 14253-1:2017.

