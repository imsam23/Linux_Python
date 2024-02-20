class PizzaBuilder:
    def __init__(self):
        self.pizza = Pizza()

    def set_crust(self, crust):
        self.pizza.crust = crust

    def set_sauce(self, sauce):
        self.pizza.sauce = sauce

    def add_topping(self, topping):
        self.pizza.toppings.append(topping)

    def build(self):
        return self.pizza

class Pizza:
    def __init__(self):
        self.crust = None
        self.sauce = None
        self.toppings = []

    def __str__(self):
        return f'Pizza with {self.crust}, {self.sauce}, and {self.toppings}'

# Usage
pizza_builder = PizzaBuilder()
pizza_builder.set_crust('thin crust')
pizza_builder.set_sauce('tomato sauce')
pizza_builder.add_topping('pepperoni')
pizza_builder.add_topping('cheese')

pizza = pizza_builder.build()

print(pizza)  # Outputs 'Pizza with thin crust, tomato sauce, and [pepperoni, cheese]'
