
"""
Use of ellipse
"""
"""
Here before '/', we can only use positional args.
After '*', we can use only kw args
IMP: between '/' and '*', we can use positional or kw args.
"""
def f(a, /, c, *, d):
    print(f'{a}-{c}-{d}')
f(2,c=3,d=4)



