class Meal:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def show_items(self):
        for item in self.items:
            print(f"Item: {item.name}, Packing: {item.packing}, Price: {item.price}")


class Item:
    def __init__(self):
        self.name = None
        self.packing = None
        self.price = None


class Burger(Item):
    def __init__(self):
        self.name = "Burger"
        self.packing = "Wrapper"
        self.price = 4.50


class Drink(Item):
    def __init__(self):
        self.name = "Drink"
        self.packing = "Bottle"
        self.price = 1.50


class MealBuilder:
    def prepare_veg_meal(self):
        meal = Meal()
        meal.add_item(Burger())
        meal.add_item(Drink())
        return meal

    def prepare_non_veg_meal(self):
        meal = Meal()
        meal.add_item(Burger())
        burger = Burger()
        burger.name = "Chicken Burger"
        meal.add_item(burger)
        meal.add_item(Drink())
        return meal


# Usage
builder = MealBuilder()

veg_meal = builder.prepare_veg_meal()
print("Veg Meal:")
veg_meal.show_items()

non_veg_meal = builder.prepare_non_veg_meal()
print("\nNon-Veg Meal:")
non_veg_meal.show_items()
