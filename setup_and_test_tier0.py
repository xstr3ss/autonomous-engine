import os
import ast

# 1. Build the Test Environment
files_to_create = {
    "models.py": """class Item:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price
""",
    "cart.py": """from models import Item

class ShoppingCart:
    def __init__(self):
        self.items = []

    def add_item(self, item: Item):
        self.items.append(item)

    def calculate_total(self) -> float:
        # BUG: Destroys cart data!
        total = 0
        while self.items:
            total += self.items.pop().price
        return total
""",
    "test_cart.py": """from models import Item
from cart import ShoppingCart

def test_calculate_total_preserves_cart():
    cart = ShoppingCart()
    cart.add_item(Item("Laptop", 1000.0))
    cart.add_item(Item("Mouse", 50.0))
    
    total = cart.calculate_total()
    
    assert total == 1050.0
    assert len(cart.items) == 2, "Cart should not be empty!"
"""
}

for filename, content in files_to_create.items():
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
print("✅ Test environment built.")

# 2. Run Tier 0 Deterministic AST Parser
def find_local_imports(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except Exception as e:
        return []
        
    local_files = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if os.path.exists(f"{node.module}.py"):
                local_files.add(f"{node.module}.py")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if os.path.exists(f"{alias.name}.py"):
                    local_files.add(f"{alias.name}.py")
    return list(local_files)

print("🔍 Tier 0 parsing AST tree for 'test_cart.py'...")
dependencies = find_local_imports("test_cart.py")

# Ensure test_cart.py is included in the final context
final_context_files = ["test_cart.py"] + dependencies
print(f"🔗 Tier 0 mapped codebase dependencies: {final_context_files}")

