# Mesure de débit d’air par plaques et caissons à tuyères

Charger cette référence pour une étude de débit d’air utilisant une pression différentielle, une plaque à orifice, une tuyère, un Venturi ou un caisson multi-tuyères. Elle complète le parcours GUM ; elle ne remplace pas le texte autorisé de la méthode métier applicable.

## Porte d’applicabilité documentaire

Identifier le montage avant de choisir une référence : conduite circulaire en charge, tuyère débouchant depuis une chambre, caisson multi-tuyères, banc d’essai de ventilateur ou étalon de transfert. Ne pas appliquer une norme uniquement parce que son titre contient « débit » ou « ventilateur ».

Corpus candidat à qualifier par `NORM-EXPERT` :

- **ISO 5801:2017**, avec **ISO 5801:2017/Amd 1:2025** : essais de performance des ventilateurs dans des conduits normalisés. Pertinente lorsque le banc sert à caractériser un ventilateur ; elle n’est pas automatiquement la méthode d’étalonnage de tout débitmètre.
- **ANSI/AMCA 210-25 / ANSI/ASHRAE 51-25** : essais aérodynamiques de ventilateurs et dispositions de chambres multi-tuyères.
- **ANSI/ASHRAE 41.7-2025** : méthodes de mesure de débit de gaz ; vérifier l’édition contractuelle et le montage couvert.
- **ISO 5167-1:2022**, **ISO 5167-2:2022** et **ISO 5167-3:2022** : exigences générales, plaques à orifice, tuyères et Venturi-tuyères insérés dans des conduites circulaires en charge. Une plaque placée sur une face de caisson ou utilisée comme étalon de transfert n’entre pas automatiquement dans leur domaine.
- **CIPM-2007** : équation d’état recommandée pour calculer la masse volumique de l’air humide et son incertitude.

Tant que le texte normatif applicable n’est pas fourni, conserver ces normes au statut `metadata_only`, ne citer aucune clause et écrire l’action de vérification nécessaire.

## Convention du modèle de tuyère

Pour une géométrie couverte par la méthode choisie, écrire le modèle sous une forme qui rend visibles le facteur de Bernoulli, la détente du gaz et les corrections géométriques :

$$
Q_m = 3600\sum_{i=1}^{N}
C_i\,\varepsilon_i\,\Phi_i\,A_i
\sqrt{2\rho_1\Delta p_i},
\qquad A_i=\frac{\pi d_i^2}{4}.
$$

Dans cette écriture :

- $C_i$ est le coefficient de décharge de la tuyère ;
- $\varepsilon_i$ est le facteur de détente ou d’expansibilité du gaz ;
- $\Phi_i$ regroupe uniquement les corrections géométriques ou de vitesse d’approche exigées par la méthode applicable ;
- $\rho_1$ est la masse volumique amont dans les conditions définies ;
- $\Delta p_i$ est la pression différentielle définie par le montage ;
- le facteur 3600 convertit des secondes vers les heures lorsque les autres unités sont cohérentes.

Une formule issue d’un rapport ou d’un logiciel peut employer un coefficient global $\alpha_i$. Exiger alors une convention explicite parmi, par exemple :

$$
\alpha_i=C_i\varepsilon_i\Phi_i
\quad\text{avec}\quad
Q_m=3600\sum_i\alpha_iA_i\sqrt{2\rho_1\Delta p_i},
$$

ou

$$
\alpha_i^{\star}=\sqrt{2}\,C_i\varepsilon_i\Phi_i
\quad\text{avec}\quad
Q_m=3600\sum_i\alpha_i^{\star}A_i\sqrt{\rho_1\Delta p_i}.
$$

Ne jamais passer d’une convention à l’autre sans transformer les coefficients et tracer la transformation. Si la définition de $\alpha_i$ est inconnue, le modèle est non identifiable et le calcul final reste `INCOMPLET`.

Le facteur $\varepsilon_i$ ne peut être omis que si la méthode applicable l’autorise ou si son écart à 1 est démontré négligeable au regard de l’objectif. Dans ce dernier cas, enregistrer l’effet comme `excluded` avec preuve ou comme composante résiduelle. Distinguer ce facteur de détente du facteur thermodynamique de compressibilité $Z$ utilisé dans l’équation de masse volumique.

## Masse volumique de l’air humide

Pour CIPM-2007, la structure de l’équation est :

$$
\rho_a=\frac{pM_a}{ZRT}
\left[1-x_v\left(1-\frac{M_v}{M_a}\right)\right].
$$

Conserver comme entrées physiques séparées la pression absolue $p$, la température thermodynamique $T$, la fraction molaire de vapeur d’eau $x_v$, le facteur $Z$ et les constantes effectivement utilisées. Une pression atmosphérique par défaut n’est pas une mesure. Versionner l’implémentation et propager l’incertitude de ses entrées.

## Séparation des budgets et prévention du double comptage

Déclarer `budget_scope` dans toute opération `uncertainty-study` :

- `bench` : seulement les composantes propriétaires `bench` et `shared` ;
- `reference` : seulement `reference` et `shared` ;
- `transfer` : seulement `transfer` et `shared` ;
- `comparison` : budget de l’écart ou de la comparaison, avec propriétaires séparés et covariances explicites ;
- `overall` : uniquement lorsqu’un mesurande global justifie réellement plusieurs propriétaires.

Pour $d=Q_{banc}-Q_{ref}$ :

$$
u^2(d)=u^2(Q_{banc})+u^2(Q_{ref})
-2\operatorname{cov}(Q_{banc},Q_{ref}).
$$

Une plaque ou une référence de transfert ne figure pas comme composante directe dans $u_c(Q_{banc})$ lorsqu’elle sert seulement à la comparaison. Si elle a servi à identifier $C_i$, $\alpha_i$ ou une fonction de correction, son incertitude doit être portée par l’incertitude et la covariance des paramètres calibrés ; enregistrer alors l’influence de la plaque comme `covered` par la composante correspondante. Ne pas ajouter simultanément la plaque, les paramètres calibrés et la correction complète.

Construire pour chaque source une chaîne unique `preuve → grandeur d’entrée → composante → budget`. Une source peut influencer plusieurs paramètres corrélés, mais ne doit pas être recomptée comme plusieurs effets indépendants.

## Contrôles minimaux avant calcul

1. Vérifier le domaine géométrique et les limites de Reynolds, pression et rapport de diamètres de la méthode retenue.
2. Déclarer la convention de $C_i$, $\alpha_i$, $\varepsilon_i$, $\Phi_i$ et le facteur $\sqrt{2}$.
3. Mesurer la pression absolue réellement utilisée pour $\rho_a$.
4. Vérifier l’unité du débit et la conversion temporelle.
5. Séparer données d’étalonnage et données de validation.
6. Déclarer le périmètre du budget et l’affectation de chaque propriétaire.
7. Vérifier les covariances créées par une même plaque, un même capteur ou un même ajustement.

## Sources primaires à consulter

- ISO, [ISO 5801:2017](https://www.iso.org/standard/56517.html) et [amendement 1:2025](https://www.iso.org/standard/88365.html).
- ISO, [ISO 5167-2:2022](https://www.iso.org/standard/79180.html) et [ISO 5167-3:2022](https://www.iso.org/standard/84845.html).
- AMCA, [ANSI/AMCA 210-25 / ANSI/ASHRAE 51-25](https://www.amca.org/publish/publications-and-standards/amca-standards/amca-%EF%BB%BFstandard-210-07-laboratory-methods-of-testing-fans-for-certified-aerodynamic-performance-rating.html).
- ASHRAE, [titres, objets et domaines des standards de mesure](https://resourcecenter.ashrae.org/technical-resources/standards-and-guidelines/titles-purposes-and-scopes).
- Picard et al., [Revised formula for the density of moist air (CIPM-2007)](https://doi.org/10.1088/0026-1394/45/2/004).
