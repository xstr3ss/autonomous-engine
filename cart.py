from models import Item

class ShoppingCart:
    def __init__(self):
        self.items = []

    def add_item(self, item: Item):
        self.items.append(item)

    def calculate_total(self) -> float:
        # Corrected: Calculate total by iterating over the items list
        total = 0
        for item in self.items:
            total += item.price
        return total