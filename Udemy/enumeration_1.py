"""

"""
from enum import Enum

class Colour(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


print(dir(Colour.RED.name))
print(Colour.RED == 1) # False
print(Colour.RED == Colour.GREEN) # True
print(Colour(1))
print(Colour['GREEN']) # If value of RED and GREEN are same then it will give the o/p as RED
print(list(Colour)) # [<Colour.RED: 1>, <Colour.GREEN: 2>, <Colour.BLUE: 3>]

class Status(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'

class UnitVector(Enum):
    V1D = (1, )
    V2D = (1, 1)
    V3d = (1, 1, 1)


print(Status.PENDING.name)
print(Status.PENDING.value)