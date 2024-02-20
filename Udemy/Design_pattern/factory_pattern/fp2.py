class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"

class AnimalFactory:
    def create_animal(self, animal_type):
        if animal_type == "dog":
            return Dog()
        elif animal_type == "cat":
            return Cat()
        else:
            raise ValueError("Invalid animal type")

# Client code
factory = AnimalFactory()

animal1 = factory.create_animal("dog")
print(animal1.speak())  # Output: Woof!

animal2 = factory.create_animal("cat")
print(animal2.speak())  # Output: Meow!
