class Dog:
    def __init__(self, name):
        self._name = name

    def speak(self):
        pass

    @classmethod
    def create(cls, name):
        if name == "poodle":
            return Poodle(name)
        elif name == "labrador":
            return Labrador(name)
        else:
            raise ValueError(f"Unknown dog type: {name}")


class Poodle(Dog):
    def speak(self):
        return "Bark! I'm a poodle."


class Labrador(Dog):
    def speak(self):
        return "Bark! I'm a labrador."


# Usage
my_dog = Dog.create("poodle")
print(my_dog.speak())  # Output: Bark! I'm a poodle.
