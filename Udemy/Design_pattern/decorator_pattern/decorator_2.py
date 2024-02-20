class MyDecorator:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        # Add extra behaviour before the function call
        print('HI')
        result = self.func(*args, **kwargs)
        # Add extra behavior after the function call
        return result

@MyDecorator
def my_function():
    print('Hello World')

my_function()
