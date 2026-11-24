# Exécution structurée et vérifiable

## But

Le mode structuré relie une proposition d'agent au noyau Python sans donner au modèle de langage l'autorité numérique. La CLI et l'orchestrateur utilisent la même interface `DeterministicEngine` et les mêmes validations.

## Enveloppe d'agent

Un adaptateur peut continuer à rendre une chaîne de texte ordinaire. Pour demander un calcul, il rend à la place un objet JSON complet :

```json
{
  "message": "Le modèle est linéaire sur le domaine étudié. La corrélation reste à confirmer.",
  "calculation_requests": [
    {
      "id": "budget-principal",
      "operation": "budget",
      "payload": {
        "coverage_factor": 2.0,
        "correlations": [],
        "components": [
          {
            "name": "bench",
            "standard_uncertainty": 0.3,
            "sensitivity": 1.0,
            "sensitivity_unit": "1",
            "owner": "bench",
            "unit": "kPa",
            "distribution": "unspecified",
            "source": "user_request",
            "degrees_of_freedom": null
          }
        ],
        "output_unit": "kPa"
      }
    }
  ]
}
```

Les opérations natives sont `budget`, `uncertainty-study`, `compare`, `paired` et `separate`. `uncertainty-study` impose le parcours Ishikawa, modèle, Type A/B et composition, puis produit une note Markdown/LaTeX et une vérification matricielle indépendante dans la même trace. Les modules déclaratifs actifs apparaissent aussi dans `available_calculation_modules` et deviennent des opérations autorisées. Le `payload` suit exactement le contrat du module. Les identifiants doivent être uniques dans le tour et un maximum de seize calculs est accepté par réponse.

Lorsqu'une requête provient de `MODEL-COMPILER`, chaque nombre, booléen et unité critique du payload doit être couvert par `evidence` :

```json
{
  "id": "budget-texte",
  "operation": "budget",
  "payload": {
    "components": [
      {
        "name": "u1",
        "standard_uncertainty": 3.0,
        "sensitivity": 1.0,
        "sensitivity_unit": "1",
        "owner": "bench",
        "unit": "kPa",
        "distribution": "unspecified",
        "source": "user_request",
        "degrees_of_freedom": null
      }
    ],
    "correlations": [],
    "coverage_factor": 2.0,
    "output_unit": "kPa"
  },
  "evidence": [
    {
      "field_path": "/components/0/standard_uncertainty",
      "source_ref": "user_request",
      "excerpt": "u1 = 3,0 kPa",
      "evidence_type": "provided"
    },
    {
      "field_path": "/components/0/sensitivity",
      "source_ref": "declared:method",
      "excerpt": "coefficient de sensibilité 1,0 déclaré",
      "evidence_type": "method_choice"
    },
    {
      "field_path": "/components/0/sensitivity_unit",
      "source_ref": "declared:method",
      "excerpt": "unité de sensibilité 1 déclarée",
      "evidence_type": "method_choice"
    },
    {
      "field_path": "/components/0/unit",
      "source_ref": "user_request",
      "excerpt": "u1 = 3,0 kPa",
      "evidence_type": "provided"
    },
    {
      "field_path": "/coverage_factor",
      "source_ref": "declared:method",
      "excerpt": "facteur de couverture 2,0 déclaré",
      "evidence_type": "method_choice"
    },
    {
      "field_path": "/output_unit",
      "source_ref": "user_request",
      "excerpt": "u1 = 3,0 kPa",
      "evidence_type": "provided"
    }
  ],
  "assumptions": ["Les corrélations sont supposées nulles."]
}
```

Le moteur contrôle le pointeur, la présence de l'extrait dans une source admise et la valeur déclarée. Les sources admises sont `user_request`, `knowledge:<id>`, `calculation:<id>`, `pdf:<document_id>` et `web:<sha256>`. Les sorties narratives d'agents sont exclues. `method_choice` et `assumption` exigent une source `declared:` et produisent une provenance `conditional`.

Une enveloppe peut aussi contenir jusqu'à quatre `module_proposals`. Elles sont validées et persistées comme candidates si l'orchestrateur possède un `ModuleStore`. Elles ne deviennent jamais actives sans promotion humaine séparée.

`WEB-RESEARCHER` peut ajouter jusqu'à huit `research_requests` pendant `plan_research` ou `refine_research` :

```json
{
  "message": "Recherche de la publication officielle courante.",
  "research_requests": [
    {
      "id": "gum-official",
      "query": "JCGM GUM official current publication",
      "purpose": "Vérifier le statut et l'édition",
      "allowed_domains": ["bipm.org"],
      "primary_sources_only": true,
      "max_results": 5
    }
  ]
}
```

Les autres rôles et la phase de synthèse reçoivent un refus s'ils tentent de déclencher une recherche. Un `ResearchProvider` absent produit également un refus visible. Les résultats sont sérialisés dans `internet_research` avec leurs URL, dates, types et empreintes.

## Résultats

L'orchestrateur ajoute chaque exécution au tour de l'agent :

```json
{
  "request": {
    "id": "budget-principal",
    "operation": "budget",
    "payload": {}
  },
  "status": "ok",
  "result": {}
}
```

Une entrée invalide n'est ni corrigée ni supprimée silencieusement :

```json
{
  "status": "rejected",
  "error_type": "ScientificValidationError",
  "error": "incompatible uncertainty component units: pressure='kPa', temperature='degC'"
}
```

`METRO-AUDIT` reçoit ces enregistrements dans `deterministic_calculations`. Un statut `ok` confirme l'arithmétique des entrées, pas la validité du modèle, la provenance des valeurs ou l'applicabilité documentaire.

## Vérification de conclusion

La conclusion finale peut déclarer :

```json
{
  "message": "L'incertitude-type composée vaut 5,0 kPa.",
  "conclusion_claims": [
    {
      "request_id": "budget-texte",
      "result_pointer": "/combined_standard_uncertainty",
      "stated_value": 5.0,
      "unit": "kPa",
      "statement": "L'incertitude-type composée vaut 5,0 kPa."
    }
  ]
}
```

Après le dernier tour, `ConclusionVerifier` compare automatiquement valeur et unité, refuse les calculs inconnus/rejetés et signale tout calcul réussi non couvert. Ce mécanisme ne valide pas une interprétation scientifique non numérique.

## Invariants appliqués

- toute valeur numérique critique doit être finie ;
- le facteur de couverture doit être fini et strictement positif ;
- chaque contribution `sensibilité × incertitude d'entrée` doit être dimensionnellement compatible avec l'unité de sortie ;
- les conversions cohérentes sont appliquées avant la propagation, y compris pour les coefficients de sensibilité typés ;
- une corrélation non nulle exige une justification écrite ;
- la matrice de corrélation doit être semi-définie positive ;
- une covariance issue d'une séparation respecte la borne de Cauchy-Schwarz ;
- une séparation exige confirmation et justification écrite de l'identifiabilité ;
- `METRO-AUDIT` est placé en dernière étape lorsque l'audit est obligatoire.

## Limite de sécurité

Les sorties narratives antérieures sont sérialisées sous `untrusted_agent_response`. Cette séparation réduit les confusions accidentelles, mais l'adaptateur fournisseur doit encore conserver les rôles système/utilisateur, limiter les outils accessibles et appliquer sa politique de confidentialité.
