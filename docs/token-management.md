# Prompt maître et gestion des tokens

## Fichiers à modifier

Le prompt opérationnel principal se trouve dans :

`src/metro_master/resources/prompts/metro-master.md`

Les règles communes de sobriété se trouvent dans :

`src/metro_master/resources/prompts/token-budget.md`

Les valeurs chiffrées sont séparées du texte et se trouvent dans :

`src/metro_master/resources/token-budget.json`

Cette séparation permet de modifier la personnalité et le workflow sans changer les plafonds, ou d'ajuster les plafonds sans réécrire le prompt.

## Profils fournis

| Profil | Usage | Plafond estimé | Sortie maximale par appel | Tours agents maximum | Réserve audit |
|---|---|---:|---:|---:|---:|
| `eco` | question ciblée, contrôle rapide | 24 000 | 1 000 | 7 | 5 000 |
| `standard` | étude métrologique habituelle | 80 000 | 2 500 | 11 | 12 000 |
| `deep` | dossier complexe explicitement demandé | 180 000 | 5 000 | 14 | 25 000 |

Les nombres sont des plafonds conservateurs pour une étude complète, pas des objectifs de consommation.

## Fonctionnement

Avant l'exécution, le profil limite le nombre de rôles. `METRO-AUDIT` et les rôles scientifiques prioritaires sont conservés. Les rôles retirés sont enregistrés dans `token_budget.skipped_steps`.

À chaque appel, le moteur estime séparément les tokens du prompt système, de la demande et du contexte partagé. Il compacte d'abord les anciennes réponses narratives et les connaissances secondaires. Les valeurs structurées, unités, calculs, sources et réserves ne sont pas supprimés silencieusement.

L'orchestrateur réserve une partie du budget total pour l'audit final. Lorsqu'un adaptateur LLM accepte le paramètre facultatif `max_output_tokens`, METRO-MASTER lui transmet la limite calculée. Dans le cas contraire, la limite est seulement inscrite dans le prompt et la sortie réelle est mesurée après réception.

## Commandes

Prévisualiser le routage limité :

```powershell
metro-master token-plan "Caractériser un banc par comparaison" --mode eco
metro-master token-plan "Caractériser un banc par comparaison" --mode standard
```

Composer un prompt avec un profil donné :

```powershell
metro-master prompt METRO-MASTER --token-mode eco
metro-master prompt METRO-MASTER --token-mode standard
metro-master prompt METRO-MASTER --token-mode deep
```

Utiliser une configuration personnalisée sans modifier celle du paquet :

```powershell
metro-master token-plan "Ma demande" --mode custom --config chemin\tokens.json
```

Le profil `custom` doit exister dans le fichier indiqué. Le schéma est identique à `resources/token-budget.json`.

## Limite importante

L'estimation locale n'est ni le tokenizer ni le compteur de facturation du fournisseur. La protection devient stricte sur la longueur de sortie seulement si l'adaptateur transmet `max_output_tokens` à l'API utilisée. Le rapport indique donc toujours `estimates_only: true`.
