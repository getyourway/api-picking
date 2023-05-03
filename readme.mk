

Récupérer les préparations de commandes non terminées:

curl -X GET http://127.0.0.1:5000/api/order_preparations


Récupérer une préparation de commande spécifique (remplacez <order_id> par un identifiant de commande existant):

curl -X GET http://127.0.0.1:5000/api/order_preparations/<order_id>


Mettre à jour une préparation de commande (remplacez <order_id> par un identifiant de commande existant et ajoutez les données de mise à jour appropriées):

curl -X PUT -H "Content-Type: application/json" -d '{"status": "completed", "items": [{"product_id": "P001", "quantity": 5}]}' http://127.0.0.1:5000/api/order_preparations/<order_id>


Créer une nouvelle préparation de commande:
curl -X POST -H "Content-Type: application/json" -d '{"status": "not_started", "items": [{"product_id": "P002", "quantity": 3}]}' http://127.0.0.1:5000/api/order_preparations