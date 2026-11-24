# Prompts des agents

Les sources versionnées des instructions se trouvent dans `src/metro_master/resources/prompts/`.

Chaque prompt complet est la concaténation du contrat commun et du rôle. Pour éviter une copie incomplète, utilisez :

```powershell
metro-master prompt METRO-MASTER
metro-master prompt PDF-EXTRACTOR
metro-master prompt WEB-RESEARCHER
metro-master prompt THEORIA
metro-master prompt GUM-EXPERT
metro-master prompt METRO-COMPARE
metro-master prompt CALIB-EXPERT
metro-master prompt DATA-METRO
metro-master prompt UNCERTAINTY-ANALYST
metro-master prompt MODEL-COMPILER
metro-master prompt PHYS-METRO
metro-master prompt NORM-EXPERT
metro-master prompt MODULE-BUILDER
metro-master prompt METRO-AUDIT
```

Cette commande produit les instructions intégrales prêtes à être copiées dans ChatGPT ou envoyées par l'orchestrateur Python.

