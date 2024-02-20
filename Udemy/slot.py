class Person:
    __slots__ = 'name',

    def __init__(self, name):
        self.name = name


class Student(Person):
    pass


class Employee(Person):
    __slots__ = 'age', 'emp_id',

    def __init__(self, name, age, emp_id):
        super().__init__(name)
        self.age = age
        self.emp_id = emp_id

p = Person('Eric')
# print(p.__dict__) # AttributeError: 'Person' object has no attribute '__dict__'. Did you mean: '__dir__'?

s = Student('Alex')
print(s.__dict__)  # Student instance has Empty dictionary

emp = Employee('Sam', 21, 100)
print(emp.__dict__)  # AttributeError: 'Employee' object has no attribute '__dict__'
