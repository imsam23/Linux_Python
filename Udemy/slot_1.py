class Person:
    """
    Descriptors are class which implement __get__ and __set__
    """
    __slots__ = '_name', 'age',

    def __init__(self, name, age):
        self.name = name
        self.age = age

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name


p = Person('Sam', 100)
# print(p.__dict__)  # 'Person' object has no attribute '__dict__'
print(type(Person.name), type(Person.age))  # <class 'property'> <class 'member_descriptor'>
# we can say that slot and property are same as both has dunder get and set method
print(hasattr(Person.name, '__get__'), hasattr(Person.name, '__set__'))
print(hasattr(Person.age, '__get__'), hasattr(Person.age, '__set__'))
