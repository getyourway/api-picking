import csv
import requests
from datetime import datetime

class Keypad:
    def __init__(self, api_url):
        self.api_url = api_url
        self.pickings = []
        self.selected_picking = None

    def fetch_pickings(self):
        url = f"{self.api_url}/api/picking"
        response = requests.get(url)
        if response.status_code == 200:
            self.pickings = response.json()
            return self.pickings
        else:
            return None

    def select_picking(self, picking_id):
        url = f"{self.api_url}/api/picking/{picking_id}"
        response = requests.get(url)
        if response.status_code == 200:
            self.selected_picking = response.json()
            self.save_picking_to_csv()
            return self.selected_picking
        else:
            return None

    def save_picking_to_csv(self):
        with open(f"keypad_local/picking_{self.selected_picking['id']}.csv", "w", newline="") as csvfile:
            fieldnames = [
                "id",
                "location",
                "item",
                "description",
                "totqty",
                "job_id",
                "item2",
                "description3",
                "um",
                "tot_needed",
                "tot_issued",
                "picked_qty",
                "picked_time",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in self.selected_picking["order_items"]:
                filtered_item = {k: v for k, v in item.items() if k in fieldnames}
                writer.writerow(filtered_item)

    def update_picking(self, picking_id, csv_file_path, finish=False):
        order_items = []
        with open(csv_file_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row["picking_order_id"] = picking_id
                if row["picked_qty"] == "":
                    row["picked_qty"] = None
                elif row["picked_qty"] is not None:
                    row["picked_qty"] = float(row["picked_qty"])
                order_items.append(row)

        url = f"{self.api_url}/api/picking/{picking_id}"
        data = {"id": picking_id, "order_items": order_items}
        if finish:
            data["status"] = "finished"

        response = requests.put(url, json=data)
        if response.status_code == 200:
            self.selected_picking = response.json()
            self.save_picking_to_csv()
            return {"status": "updated"}
        else:
            print(f"Error updating picking {picking_id}: {response.status_code}, {response.text}")
            return None

def main():
    api_url = "http://localhost:5000"
    keypad = Keypad(api_url)

    # Fetch pickings
    pickings = keypad.fetch_pickings()
    if pickings:
        print("Pickings available:")
        for picking in pickings:
            print(f"{picking['id']}: {picking['status']}")
    else:
        print("Error fetching pickings")

    # Select picking
    picking_id = int(input("Enter picking ID to select: "))
    selected_picking = keypad.select_picking(picking_id)
    if selected_picking:
        print(f"Picking {picking_id} selected")
    else:
        print("Error selecting picking")

    # Choose action
    print("1 - Send modified picking")
    print("2 - Finish picking")
    action = None
    while action not in ["1", "2"]:
        action = input("Enter a valid action: ")

    # Update picking
    csv_file_path = f"keypad_local/picking_{picking_id}.csv"
    updated_picking = keypad.update_picking(picking_id, csv_file_path, action == "2")
    if updated_picking:
        print(f"Picking {picking_id} updated")
    else:
        print("Error updating picking")

if __name__ == "__main__":
    main()
