"""
Dependency Inversion Principle:
 The dependency inversion principle (DIP) is a software design principle that states
 that high-level modules should not depend on low-level modules.
 Both should depend on abstractions. Abstractions should not depend on details.
 Details should depend on abstractions.

 DIP states that high-level modules should not be coupled to the concrete implementation details of
 low-level modules. Instead, both high-level and low-level modules should depend on abstractions,
 such as interfaces or abstract classes.

"""

# Without DIP:

class File:
    def read(self):
        pass

class HighLevelModule:
    def do_something(self):
        file = File()
        file.read()

# With DIP:

class FileInterface:
    def read(self):
        pass

class File(FileInterface):
    def read(self):
        pass

class HighLevelModule:
    def __init__(self, file_interface: FileInterface):
        self.file_interface = file_interface

    def do_something(self):
        self.file_interface.read()