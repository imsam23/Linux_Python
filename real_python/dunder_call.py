import pdb

"""
Sometimes, you may want to write callable objects that retain state between calls,
which are commonly known as stateful callables. 
For example, say that you want to write a callable that takes consecutive numeric values 
from a data stream and computes their cumulative average. Between calls, the callable must 
keep track of previously passed values.
"""


def cumulative_average():
    data = []

    def average(new_value):
        data.append(new_value)
        return sum(data) / len(data)

    return average


stream_average = cumulative_average()
print(stream_average(12))
print(stream_average(13))


class CumulativeAverager:
    def __init__(self):
        self.data = []

    def __call__(self, new_value):
        self.data.append(new_value)
        return sum(self.data) / len(self.data)


stream_average = CumulativeAverager()
print(stream_average(12))
print(stream_average(13))


# ============================

# factorial.py

class Factorial:
    def __init__(self):
        self.cache = {0: 1, 1: 1}

    def __call__(self, number):
        if number not in self.cache:
            self.cache[number] = number * self(number - 1)  # self is callable
        return self.cache[number]


factorial_of = Factorial()
print(factorial_of(4))
###########################################################################
import time


#  you can also write class-based decorators by taking advantage of the .__call__() special method.
class ExecutionTimer:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        start = time.perf_counter()
        result = self.func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{self.func.__name__}() took {(end - start) * 1000:.4f} ms")
        return result


@ExecutionTimer
def square_numbers(numbers):
    return [number ** 2 for number in numbers]


square_numbers(list(range(5)))


###########################################################################


class ExecutionTimer:
    def __init__(self, repetitions=1):
        self.repetitions = repetitions

    def __call__(self, func):
        def timer(*args, **kwargs):
            result = None
            total_time = 0
            print(f"Running {func.__name__}() {self.repetitions} times")
            for _ in range(self.repetitions):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                end = time.perf_counter()
                total_time += end - start
            average_time = total_time / self.repetitions
            print(
                f"{func.__name__}() takes "
                f"{average_time * 1000:.4f} ms on average"
            )
            return result

        return timer


@ExecutionTimer(repetitions=3)
def square_numbers(numbers):
    return [number ** 2 for number in numbers]


square_numbers(list(range(4)))
