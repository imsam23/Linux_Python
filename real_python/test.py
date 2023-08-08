def fun():
    return 'Hello'

f = fun
print(f())
f.count = 1
f.new_attr = 2
print(f.new_attr)
