import logging

logging.basicConfig(level=logging.INFO)
"""
A descriptor is what we call any object that defines __get__(), __set__(), or __delete__().
Descriptors get invoked by the dot operator during attribute lookup.
If a descriptor is accessed indirectly with vars(some_class)[descriptor_name], the descriptor instance is returned without invoking it.
IMP: Descriptors only work when used as class variables. When put in instances, they have no effect.
If an object defines __set__() or __delete__(), it is considered a data descriptor. Descriptors that only define __get__() are called non-data descriptors.
If an instance’s dictionary has an entry with the same name as a data descriptor, the data descriptor takes precedence. 
If an instance’s dictionary has an entry with the same name as a non-data descriptor, the dictionary entry takes precedence.
To make a read-only data descriptor, define both __get__() and __set__() with the __set__() raising an AttributeError when called. 
    Defining the __set__() method with an exception raising placeholder is enough to make it a data descriptor.

"""

class LoggedAccess:

    def __set_name__(self, owner, name):
        """
         __set_name__() method:  This is only used in cases where a descriptor needs to know either the class where
         it was created or the name of class variable it was assigned to. (This method,
         if present, is called even if the class is not a descriptor.)
        Args:
            owner:
            name:

        Returns:

        """
        self.public_name = name
        self.private_name = '_' + name

    def __get__(self, obj, owner):
        value = getattr(obj, self.private_name)
        logging.info('Accessing %r giving %r', self.public_name, value)
        return value

    def __set__(self, obj, value):
        logging.info('Updating %r to %r', self.public_name, value)
        setattr(obj, self.private_name, value)

class Person:

    name = LoggedAccess()
    age = LoggedAccess()

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def birthday(self):
        self.age += 1



# If a descriptor is accessed indirectly with vars(some_class)[descriptor_name], the descriptor instance is returned without invoking it.
vars(vars(Person)['name'])
#{'public_name': 'name', 'private_name': '_name'}
vars(vars(Person)['age'])
#{'public_name': 'age', 'private_name': '_age'}


pete = Person('Peter P', 10)
print(pete)
kate = Person('Catherine C', 20)
print(kate)



