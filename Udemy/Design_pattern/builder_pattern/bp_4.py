class Person:
    def __init__(self):
        self.name = None
        self.position = None
        self.dob = None

    def __str__(self):
        return f'{self.name} born on {self.dob} and works as {self.position}'

    @staticmethod
    def new(self):
        return PersonBuilder()


class PersonBuilder:
    def __init__(self):
        self.person = Person()

    def build(self):
        return self.person


class PersonInforBuilder(PersonBuilder):
    def called(self, name):
        self.person.name = name
        return self


class PersonDateBirthBuilder(PersonInforBuilder):
    def born(self, dob):
        self.person.dob = dob
        return self


class PersonJobBuilder(PersonDateBirthBuilder):
    def works_as(self, position):
        self.person.position = position
        return self

pb = PersonJobBuilder()
me = pb.called('Sam').born('1/1/1000').works_as('Engineer').build()
print(me)
