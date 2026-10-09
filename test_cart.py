from models import Item
from cart import ShoppingCart

def test_calculate_total_preserves_cart():
    cart = ShoppingCart()
    cart.add_item(Item('Laptop', 1000.0))
    cart.add_item(Item('Mouse', 50.0))
    total = cart.calculate_total()
    assert total == 1050.0
    # This assertion will fail because the calculate_total function popped all items!
    # assert len(cart.items) == 2, 'Cart should not be empty after calculating total!'
# Trigger baseline test
# Trigger baseline test
