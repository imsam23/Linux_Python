"""
__hash__ : If we are implementing __hash__ then we must implement __new__ as well but vice versa is not true
__bool__ : if __bool__ is not defined then Python looks for __len__ method
           if neither presents then it will always return True
__call__ : We can use it for caching (cache hit/miss)
           Every class is callable but not instance
           To make instance callable , we need to implement __call__ method
           Use cases:
             -->Retain state between calls
             -->Cache values that result from previous computations
             -->Implement straightforward and convenient APIs
"""

class Person:
    def __init__(self, name):
        #self.name = name  # It is mutable so we wont be able to use it for hash
        self._name = name  # So we are making it Private variable

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        return isinstance(other, Person) and self.name == other.name

    # We want Object to be hashable so that it can be used in Dictionary
    def __hash__(self):
        return hash(self.name)

p1 = Person('Eric')
p2 = Person('Eric')
p3 = Person('Satyam')

print(p1 == p2)
print(p1 == p3)

class Mylist:
    def __init__(self, length):
        self._length = length

class Person:
    def __call__(self):
        print('__call__ called')
p = Person()
p()

#========================
def my_func(a,b,c):
    return a*b*c
class Partial:
    def __init__(self, func, *args):
        self._func = func
        self._args = args

    def __call__(self, *args):
        return self._func(*self._args, *args)

partial_func = Partial(my_func, 2, 3)
print(partial_func(4))

#===========================
from collections import defaultdict
from functools import partial

# Real python

class PowerFactory:
    def __init__(self, exponent):
        self.exponent = exponent

    def __call__(self, base):
        return base**self.exponent

squareof = PowerFactory(2)
op = squareof(3)
cubeeof = PowerFactory(3)
op = cubeeof(3)





