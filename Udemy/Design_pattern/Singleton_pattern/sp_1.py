"""
Purpose:

Ensures only one instance of a class exists throughout the program's lifetime.
Provides a global point of access to that single instance.
Common Use Cases:

Managing shared resources (e.g., database connections, hardware devices)
Logging systems
Configuration settings
Global state management
"""

# Not a good approach
# We cant use the __init__ method here as it will be called every time in this case
class Database:
    _instance = None
    # def __init__(self):
    #     print('Loading Database')

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Database, cls).__new__(cls, *args, **kwargs)

d1 = Database()
d2 = Database()
print(d1 == d2) # true
#===========================

def singleton(class_):
     instances = {}

     def get_instances(*args, **kwargs):
         if class_ not in instances:
             instances[class_] = class_(*args, **kwargs)
         return instances[class_]
     return get_instances


@singleton
class Database:
    def __init__(self):
        print('Loading Database')

d1 = Database()
d2 = Database()
print(d1==d2)
vibgyor
