class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        return self.height

    @height.setter
    def height(self, value):
        self.height = value

    def area(self):
        return self._width * self._height
