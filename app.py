import csv
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Modèles de base de données
class OrderPreparation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    order_items = db.relationship("OrderItem", backref="order_preparation", lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(10), nullable=False)
    item = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    totqty = db.Column(db.Float, nullable=False)
    job_id = db.Column(db.String(10), nullable=False)
    item2 = db.Column(db.String(10), nullable=True)
    description3 = db.Column(db.String(50), nullable=True)
    um = db.Column(db.String(10), nullable=False)
    tot_needed = db.Column(db.Float, nullable=False)
    tot_issued = db.Column(db.Float, nullable=False)
    picked = db.Column(db.Boolean, nullable=False, default=False)
    picked_qty = db.Column(db.Float, nullable=True)
    order_preparation_id = db.Column(db.Integer, db.ForeignKey("order_preparation.id"), nullable=False)

# Créer les tables de la base de données si elles n'existent pas
with app.app_context():
    db.create_all()

def load_orders_from_csv():
    orders_directory = "orders"
    for filename in os.listdir(orders_directory):
        if filename.endswith(".csv"):
            order_id = int(filename.split("_")[1].split(".")[0])
            order = OrderPreparation.query.get(order_id)
            if not order:
                order = OrderPreparation(id=order_id, status="not_started")
                db.session.add(order)
                db.session.commit()
            with open(os.path.join(orders_directory, filename), "r") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    item = OrderItem(
                        location=row["Location"],
                        item=row["Item"],
                        description=row["Description"],
                        totqty=round(float(row["Totqty"].replace(',', '.')), 3),
                        job_id=row["JobID"],
                        item2=row["item2"],
                        description3=row["description3"],
                        um=row["UM"],
                        tot_needed=round(float(row["TotNeeded"].replace(',', '.')), 3),
                        tot_issued=round(float(row["TotIssued"].replace(',', '.')), 3),
                        picked=False,
                        picked_qty=0,
                        order_preparation_id=order.id,
                    )
                    db.session.add(item)
                    db.session.commit()

with app.app_context():
    load_orders_from_csv()

# Récupérer les préparations de commandes non terminées
@app.route("/api/order_preparations", methods=["GET"])
def get_order_preparations():
    not_finished_orders = OrderPreparation.query.filter(OrderPreparation.status != "finished").all()
    return jsonify([{'id': order.id, 'status': order.status,} for order in not_finished_orders])

# Récupérer une préparation de commande spécifique
@app.route("/api/order_preparations/<int:order_id>", methods=["GET"])
def get_order_preparation(order_id):
    order = OrderPreparation.query.get(order_id)
    if order:
        return jsonify(order.to_dict())
    else:
        return "Order not found", 404

# Mettre à jour une préparation de commande
@app.route("/api/order_preparations/<int:order_id>", methods=["PUT"])
def update_order_preparation(order_id):
    logging.info(f"Updating order preparation {order_id}")
    order = OrderPreparation.query.get(order_id)
    if order:
        order_data = request.get_json()
        order.status = order_data.get("status", order.status)

        # Mettre à jour les éléments de commande existants
        items_data = order_data.get("order_items", [])
        for item_data in items_data:
            item_id = item_data["id"]
            item = OrderItem.query.get(item_id)
            if item:
                item.picked = item_data["picked"]
                item.picked_qty = item_data["picked_qty"]
                logging.info(f"Updated order_item {item_id}")

        db.session.commit()
        logging.info(f"Finished updating order preparation {order_id}")
        return jsonify(order.to_dict())
    else:
        logging.warning(f"Order preparation {order_id} not found")
        return "Order not found", 404

def order_preparation_to_dict(self):
    return {
        "id": self.id,
        "status": self.status,
        "order_items": [
            {
                "id": item.id,
                "location": item.location,
                "item": item.item,
                "description": item.description,
                "totqty": item.totqty,
                "job_id": item.job_id,
                "item2": item.item2,
                "description3": item.description3,
                "um": item.um,
                "tot_needed": item.tot_needed,
                "tot_issued": item.tot_issued,
                "picked": item.picked,
                "picked_qty": item.picked_qty,
                "order_preparation_id": item.order_preparation_id,
            }
            for item in self.order_items
        ],
    }

OrderPreparation.to_dict = order_preparation_to_dict

if __name__ == "__main__":
    app.run(debug=True)

