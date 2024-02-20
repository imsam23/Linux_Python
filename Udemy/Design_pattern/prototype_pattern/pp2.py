from abc import ABC, abstractmethod


class Prototype(ABC):
    @abstractmethod
    def clone(self):
        pass


class ConcretePrototype1(Prototype):
    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2

    def clone(self):
        return ConcretePrototype1(self.field1, self.field2)


class ConcretePrototype2(Prototype):
    def __init__(self, field3):
        self.field3 = field3

    def clone(self):
        return ConcretePrototype2(self.field3.copy())  # Deep copy for mutable fields


prototype1 = ConcretePrototype1("value1", 42)
prototype2 = ConcretePrototype2([1, 2, 3])

clone1 = prototype1.clone()  # Create a clone of prototype1
clone2 = prototype2.clone()  # Create a clone of prototype2

print(clone1.field1, clone1.field2)  # Output: value1 42
print(clone2.field3)  # Output: [1, 2, 3] (separate list)

