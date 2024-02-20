from enum import Enum

"""
OCP = Open Closed Principle
A class should be open for extension and closed for modification
"""


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class Size(Enum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class Product:
    def __init__(self, name, color, size):
        self.name = name
        self.color = color
        self.size = size


# class ProductFilter:
#     # we can create method like
#     # filter_by_color or filter_by_size or filter_by_color_size
#     pass


class Specification:
    def is_satisfied(self, item):
        pass

    def __and__(self, other):
        return AndSpecification(self, other)


class Filter:
    def filter(self, item, spec):
        pass


class ColorSpecification(Specification):
    def __init__(self, color):
        self.color = color

    def is_satisfied(self, item):
        return item.color == self.color


class SizeSpecification(Specification):
    def __init__(self, size):
        self.size = size

    def is_satisfied(self, item):
        return item.size == self.size


class AndSpecification(Specification):
    def __init__(self, *args):
        self.args = args

    def is_satisfied(self, item):
        return all(map(lambda spec: spec.is_satisfied(item), self.args))



class BetterFilter(Filter):
    def filter(self, items, spec):
        for item in items:
            if spec.is_satisfied(item):
                yield item


if __name__ == '__main__':
    apple = Product('Apple', Color.GREEN, Size.SMALL)
    tree = Product('Tree', Color.GREEN, Size.LARGE)
    house = Product('House', Color.BLUE, Size.LARGE)
    products = [apple, tree, house]

    bf = BetterFilter()
    green = ColorSpecification(Color.GREEN)
    print(f'Green Products')
    for p in bf.filter(products, green):
        print(f'- {p.name} is green')

    print(f'Large Blue Products')
    large = SizeSpecification(Size.LARGE)
    blue = ColorSpecification(Color.BLUE)
    large_blue = AndSpecification(large, blue)

    for p in bf.filter(products, large_blue):
        print(f'- {p.name} is Large and Blue')

    # If wa want to use '&' operator like below then implement __and__ in Specification class
    large_n_blue = large & blue
    for p in bf.filter(products, large_n_blue):
        print(f'- {p.name} is Large and Blue')

