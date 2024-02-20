import os


class DirectorySize:
    def __get__(self, obj, obj_ttype=None):
        return len(os.listdir(obj.dirname))


class Directory:

    size = DirectorySize()  # Descriptor instance

    def __init__(self, dir_name):
        self.dir_name = dir_name  # Regular instance attribute

"""
this example reveals the purpose of the parameters to __get__(self, obj, obj_ttype=None):
    The self parameter is size, an instance of DirectorySize. 
    The obj parameter is s, an instance of Directory. 
    It is the obj parameter that lets the __get__() method learn the target directory. 
    The objtype parameter is the class Directory
"""

current_dir = os.getcwd()
s = Directory(current_dir)
print(s.size)

