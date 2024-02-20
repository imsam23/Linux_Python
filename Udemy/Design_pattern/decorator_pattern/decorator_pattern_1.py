from abc import ABC


class Shape(ABC):
    def __str__(self):
        return ''


class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def resize(self, factor):
        self.radius *= factor

    def __str__(self):
        return f'A circle with radius {self.radius}'


class Square(Shape):
    def __init__(self, side):
        self.side = side

    def __str__(self):
        return f'A Square with side {self.side}'


class ColorShape(Shape):
    def __init__(self, shape, color):
        self.shape = shape
        self.color = color

    def __str__(self):
        return f'{self.shape} has the {self.color} color'


if __name__ == '__main__':
    """
    With this implementation we can created a decorated class object(red_circle)
      but we wont be able to access its methods/attributes. 
    """
    circle = Circle(3)
    red_circle = ColorShape(circle, 'red') # red_circle cant access the resize method here.
    print(red_circle)
