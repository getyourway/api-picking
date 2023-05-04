# Documentation de l'API de gestion des pickings

## Introduction

Cette API permet de gérer les pickings, c'est-à-dire la préparation des commandes dans un entrepôt. Elle permet de créer de nouveaux pickings, de les mettre à jour et de les consulter.

Cette API est une ébauche développée par Get Your Way dans le cadre d'un projet avec Alpha Innovations.

## Modèles de données

### PickingOrder

Représentation en DB d'un picking

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Clé primaire |
| status | String | Statut du picking (not_started, started, finished) |
| order_items | Relation | Items de la commande |

### PickingItem

Représentation en DB d'un item de picking

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Clé primaire |
| location | String | Emplacement de l'article dans l'entrepôt |
| item | String | Code de l'article |
| description | String | Description de l'article |
| totqty | Float | Quantité totale de l'article à préparer |
| job_id | String | Identifiant du travail associé à l'article |
| item2 | String | Deuxième code d'article (optionnel) |
| description3 | String | Troisième description d'article (optionnel) |
| um | String | Unité de mesure de l'article |
| tot_needed | Float | Quantité totale nécessaire de l'article |
| tot_issued | Float | Quantité totale émise de l'article |
| picked_qty | Float | Quantité prélevée de l'article |
| picked_time | DateTime | Date et heure de préparation de l'article |
| picking_order_id | Integer | Clé étrangère vers le picking associé |

### Représentation JSON d'un picking

```c
{
    "id": int,
    "status": string,
    "order_items": [
        {
            "id": int,
            "location": string,
            "item": string,
            "description": string,
            "totqty": float,
            "job_id": string,
            "item2": string,
            "description3": string,
            "um": string,
            "tot_needed": float,
            "tot_issued": float,
            "picked_time": datetime,
            "picked_qty": float,
            "picking_order_id": int
        },
        ...
    ]
}
```

## Routes de l'API

Les routes de l'API sont les suivantes:

### GET /api/picking

Cette route retourne tous les pickings non terminées. Les pickings sont représentés par un objet JSON qui contient l'identifiant et le statut du picking. Cette route ne retourne pas le contenu des commandes.

#### Exemple de réponse:

```json
[
    {
        "id": 1,
        "status": "not_started"
    },
    {
        "id": 2,
        "status": "started"
    }
]
```

#### Exemple de requête CURL

```console
$ curl -X GET http://127.0.0.1:5000/api/picking
```

### GET /api/picking/{order_id}

Cette route retourne un picking spécifique sur base de son ID. La réponse est un objet JSON qui contient l'identifiant, le statut et les éléments de commande du picking.

> Si l'ID fourni n'existe pas, la réponse est un message d'erreur **"Le picking n'a pas pu être trouvé"**.

#### Exemple de réponse:

```json
{
    "id": 1,
    "status": "not_started",
    "order_items": [
        {
            "id": 1,
            "location": "A1",
            "item": "123456",
            "description": "Description de l'article",
            "totqty": 10,
            "job_id": "JOB1",
            "item2": null,
            "description3": null,
            "um": "EA",
            "tot_needed": 10,
            "tot_issued": 0,
            "picked_time": null,
            "picked_qty": null,
            "picking_order_id": 1
        }
    ]
}
```

#### Exemple de requête CURL

```console
$ curl -X GET http://127.0.0.1:5000/api/picking/<order_id>
```

### PUT /api/picking/{order_id}

Cette route met à jour le contenu d'un picking et retourne le picking dans son état complet après mis à jour. La réponse est un objet JSON qui contient l'identifiant, le statut et tous les éléments de la commande.

> Si l'ID fourni n'existe pas, la réponse est un message d'erreur **"Le picking n'a pas pu être trouvé"**.

> Si le statut du picking est "finished", la réponse est un message d'erreur **"Le picking déjà terminé"**.

> Si certaines quantités n'ont pas été spécifiées, la réponse est un message d'erreur **"Certaines quantités n'ont pas été spécifiées"**.


#### Exemple de corps de requête

```json
{
    "order_items": [
        {
            "id": 1,
            "picked_qty": 5,
            "picked_time": "Tue, 04 May 2023 08:00:00 GMT"
        }
    ],
    "status": "finished"
}
```

#### Exemple de réponse

```json
{
    "id": 1,
    "status": "finished",
    "order_items": [
        {
            "id": 1,
            "location": "A1",
            "item": "123456",
            "description": "Description de l'article",
            "totqty": 10,
            "job_id": "JOB1",
            "item2": null,
            "description3": null,
            "um": "EA",
            "tot_needed": 10,
            "tot_issued": 0,
            "picked_time": "2023-05-04T08:00:00",
            "picked_qty": 5,
            "picking_order_id": 1
        }
    ]
}
```

#### Exemple de requête CURL

```console
$ curl -X PUT -H "Content-Type: application/json" -d '{"status": "not_started", "order_items": [{"id": "3", "picked_qty": 6}]}' http://127.0.0.1:5000/api/picking/<order_id>
```

#### Synchronisation

Seuls les articles avec une valeur pour `picked_qty` sont mis à jour. De plus, cette valeur n'est modifiée que si la date envoyée dans la requête est plus récente que celle stockée en base de données.

> Pour forcer la mise à jour sans prendre en compte la date stockée en base de données, la date doit être omise dans la requête de mise à jour. Le serveur s'occupera de mettre à jour la date sur base de l'heure à laquelle i la reçu la requête.

Afin de s'assurer que les données du préparateur de commande et celle de la base de données sont les mêmes, l'ensemble des articles de la commande est renvoyé en réponse afin que le préparateur mette à jour ses données locales.
