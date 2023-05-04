import csv
import os
from datetime import datetime
import logging

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Modèles de base de données

class PickingOrder(db.Model):
    """Représentation en DB d'un picking"""

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="not_started")
    order_items = db.relationship("PickingItem", backref="picking_order", lazy=True)

    def to_dict(self):
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
                "picked_time": item.picked_time,
                "picked_qty": item.picked_qty,
                "picking_order_id": item.picking_order_id,
            }
            for item in self.order_items
        ],
    }


class PickingItem(db.Model):
    """Représentation en DB d'un item de picking"""

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
    picked_qty = db.Column(db.Float, nullable=True)
    picked_time = db.Column(db.DateTime, nullable=True)
    picking_order_id = db.Column(db.Integer, db.ForeignKey("picking_order.id"), nullable=False)


# Créer les tables de la base de données si elles n'existent pas
with app.app_context():
    db.create_all()

def load_orders_from_csv():
    """Load picking orders from csv files into the database if they do not exist yet"""

    orders_directory = "orders"
    for filename in os.listdir(orders_directory):
        if filename.endswith(".csv"):
            order_id = int(filename.split("_")[1].split(".")[0])
            order = PickingOrder.query.get(order_id)

            if not order:
                order = PickingOrder(id=order_id, status="not_started")
                db.session.add(order)
                db.session.commit()

                # Add items to new order
                with open(os.path.join(orders_directory, filename), "r") as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        item = PickingItem(
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
                            picked_time=None,
                            picked_qty=None,
                            picking_order_id=order.id,
                        )
                        db.session.add(item)
                        db.session.commit()

with app.app_context():
    load_orders_from_csv()


# Routes API

@app.route("/api/picking", methods=["GET"])
def get_pickings():
    """Retourne tous les pickings non terminées"""

    orders = PickingOrder.query.filter(PickingOrder.status != "finished").all()

    return jsonify(
        [
            {
                "id": order.id,
                "status": order.status
            } for order in orders
        ]
    )


@app.route("/api/picking/<int:order_id>", methods=["GET"])
def get_picking(order_id):
    """Retourne un picking spécifique sur base de son ID"""

    order = PickingOrder.query.get(order_id)
    if order:
        return jsonify(order.to_dict())
    else:
        return "Le picking n'a pas pu être trouvé", 404


@app.route("/api/picking/<int:order_id>", methods=["PUT"])
def update_picking(order_id):
    """Met à jour le contenu d'un picking et retourne le picking dans son état complet après mis à jour"""

    logging.info(f"Updating order preparation {order_id}")
    order = PickingOrder.query.get(order_id)

    if not order:
        logging.warning(f"Order preparation {order_id} not found")
        return "Le picking n'a pas pu être trouvé", 404

    if order.status == "not_started":
        order.status = "started"
    elif order.status == "finished":
        return "Le picking déjà terminé", 400

    order_data = request.get_json()

    # Mettre à jour les éléments de commande existants
    items_data = order_data.get("order_items", [])
    for item_data in items_data:
        item_id = item_data["id"]

        item = PickingItem.query.get(item_id)
        if item and item_data["picked_qty"] is not None:
            # Parse picked time
            picked_time = item_data.get("picked_time")
            if picked_time:
                picked_time = datetime.strptime(picked_time, '%a, %d %b %Y %H:%M:%S %Z')
            else:
                picked_time = datetime.now()

            if item.picked_time is None or item.picked_time < picked_time:
                item.picked_qty = item_data["picked_qty"]
                item.picked_time = picked_time
                logging.info(f"Updated order_item {item_id}")

    db.session.commit()

    # Mark picking order as finished
    if "status" in order_data and order_data["status"] == "finished":
        # Check that all items have been picked
        if db.session.query(func.count(PickingItem.id)).filter(PickingItem.picking_order_id == order_id, PickingItem.picked_qty.is_(None)).scalar() == 0:
            order.status = "finished"
            db.session.commit()
        else:
            return "Certaines quantités n'ont pas été spécifiées", 400

    logging.info(f"Finished updating order preparation {order_id}")
    return jsonify(order.to_dict())


if __name__ == "__main__":
    app.run(debug=True)

