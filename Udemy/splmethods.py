
"""
1. if repr and str method is there then print method will call str method first
2. first it will search for str method then repr method"""

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __repr__(self):
        print("repr called ")
        return f"Person(name={self.name}, age={self.age})"

    def __str__(self):
        print("str called")
        return f"Person(name={self.name})"

