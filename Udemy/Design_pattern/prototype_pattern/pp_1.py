"""

Here's an explanation of the Prototype pattern in Python, along with an example:

Purpose:

Creates new objects by cloning existing ones, rather than through direct construction.
Useful when object creation is expensive or complex, or when you want to customize objects without affecting their prototypes.
Key Components:

Prototype: A base class or interface that declares a cloning method (usually clone()).
Concrete Prototypes: Classes that implement the Prototype interface and provide specific cloning functionality.
Client: Code that uses the Prototype to create new objects by cloning.

"""
import copy


class Address:
    def __init__(self, street_address, suite, city):
        self.street_address  = street_address
        self.suite = suite
        self.city = city

    def __str__(self):
        return f'Address: {self.street_address} {self.suite} {self.city} '


class Employee:
    def __init__(self, name, address):
        self.name = name
        self.address = address

    def __str__(self):
        return f'{self.name} works at {self.address}'


class EmployeeFactory:
    main_office_employee = Employee('', Address('Street_A', '', 'London'))
    aux_office_employee = Employee('', Address('Street_B', '', 'London'))

    @staticmethod
    def __new_employee(proto, name, suite):
        result = copy.deepcopy(proto)
        result.name = name
        result.suite = suite
        return result

    @staticmethod
    def new_main_office_employee(name, suite):
        return EmployeeFactory.__new_employee(EmployeeFactory.main_office_employee, name, suite)

    @staticmethod
    def aux_main_office_employee(name, suite):
        return EmployeeFactory.__new_employee(EmployeeFactory.aux_office_employee, name, suite)


Jane = EmployeeFactory.new_main_office_employee('Jane', 101)
John = EmployeeFactory.aux_main_office_employee('John', 102)
print(Jane)
print(John)





