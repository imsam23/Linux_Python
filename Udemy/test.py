class Test:
    lang = 'Python'
    version = '3.10'


print(Test.__qualname__) # class Name
print(getattr(Test, 'lang'))
