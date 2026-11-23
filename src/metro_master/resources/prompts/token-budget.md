# Contrat de sobriété contextuelle

Le budget de tokens est une limite de sécurité, jamais une cible à consommer. Le mode actif et ses valeurs chiffrées sont ajoutés ci-dessous par le moteur.

## Règles obligatoires

1. Commencer par le minimum suffisant : cadrage, routage, calcul déterministe, conclusion et audit.
2. Ne jamais charger les treize prompts, toute la bibliothèque ou tous les PDF par défaut.
3. Charger un seul rôle spécialisé à la fois et uniquement les extraits documentaires utiles à sa tâche.
4. Préférer un tableau compact, un JSON structuré ou un pointeur de preuve à la répétition d'un texte déjà présent.
5. Ne pas répéter la demande, les sorties précédentes ni les avertissements communs sauf si leur absence rendrait la conclusion ambiguë.
6. Réserver la capacité annoncée pour `METRO-AUDIT`. Aucun approfondissement facultatif ne peut consommer cette réserve.
7. Lorsque le budget devient insuffisant, terminer le calcul déterministe en cours, signaler les rôles ou sources non traités, puis passer à l'audit. Ne jamais poursuivre silencieusement.
8. Une sortie tronquée par budget reste `incomplete`. Elle ne peut pas devenir `validated` par reformulation.
9. Les estimations du moteur ne sont pas les compteurs officiels du fournisseur. Si le fournisseur communique un usage exact, celui-ci est prioritaire.

## Stratégie de compression

Compresser dans cet ordre : répétitions narratives ; anciennes réponses d'agents ; connaissances non retenues ; extraits secondaires. Ne jamais supprimer silencieusement une valeur brute utilisée, une unité, une covariance, une justification, un résultat déterministe, une source citée ou une réserve d'audit.
