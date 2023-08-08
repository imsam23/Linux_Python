from collections import deque

tasks = deque()


def fun(n):
    while n > 0:
        yield n
        n = n-1


tasks.extend([fun(3), fun(4), fun(5)])

def run():
    while tasks:
        task = tasks.popleft()
        try:
            i = next(task)
            print(i)
            tasks.append(task)
        except StopIteration:
            print('Task')

