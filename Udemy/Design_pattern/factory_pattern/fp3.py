"""
Here's a comprehensive explanation of the Factory Pattern, along with an illustrative example:

Factory Pattern:

Purpose: Encapsulates object creation logic, promoting loose coupling, flexibility, and code reusability.
Central Idea: Client code delegates object creation to a specialized factory class, instead of directly using constructors.
Key Components:
Product: The abstract interface or base class representing objects to be created.
Concrete Products: Specific classes implementing the Product interface.
Factory: Responsible for creating objects of Concrete Product types.
Client: Uses the Factory to obtain Product objects, without knowing their exact classes.
Example (Illustrative):

Imagine a pizza shop:

Product: Pizza (interface)
Concrete Products: CheesePizza, VeggiePizza, PepperoniPizza
Factory: PizzaFactory
Client: Customer

"""
class Pizza:
    def prepare(self):
        raise NotImplementedError("Subclasses must implement prepare()")

    def bake(self):
        print("Baking pizza")

    def cut(self):
        print("Cutting pizza")

    def box(self):
        print("Boxing pizza")


class CheesePizza(Pizza):
    def prepare(self):
        print("Preparing cheese pizza")


class VeggiePizza(Pizza):
    def prepare(self):
        print("Preparing veggie pizza")


class PepperoniPizza(Pizza):
    def prepare(self):
        print("Preparing pepperoni pizza")


class PizzaFactory:
    @staticmethod  # Using a static method for the factory
    def create_pizza(pizza_type):
        pizza_types = {
            "cheese": CheesePizza,
            "veggie": VeggiePizza,
            "pepperoni": PepperoniPizza
        }
        return pizza_types.get(pizza_type, None)()  # Return a new instance of the Pizza subclass


# Client code
customer = "customer"
pizza_type = "veggie"  # Can be changed dynamically
pizza = PizzaFactory.create_pizza(pizza_type)
if pizza:
    pizza.prepare()
    pizza.bake()
    pizza.cut()
    pizza.box()
else:
    print(f"Invalid pizza type '{pizza_type}' requested by {customer}")
