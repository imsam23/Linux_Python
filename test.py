import asyncio
import time
import asyncio
from typing import *

#https://www.artificialworlds.net/blog/2017/05/31/python-3-large-numbers-of-tasks-with-limited-concurrency/

"""
The keyword await passes function control back to the event loop. 
(It suspends the execution of the surrounding coroutine.) 
If Python encounters an await f() expression in the scope of g(), 
this is how await tells the event loop, 
“Suspend execution of g() until whatever I’m waiting on—the result of f()—is returned. 
In the meantime, go let something else run.”

In code, that second bullet point looks roughly like this:

async def g():
    # Pause here and come back to g() when f() is ready
    r = await f()
    return r
"""


async def fun1(n: List):
    for i in n:
        print(i)
        await asyncio.sleep(1)
        await asyncio.sleep(1)



async def fun2(n: List):
    for i in n:
        print(i)
        await asyncio.sleep(1)

async def fun3(n: List):
    for i in n:
        print(i)
        await asyncio.sleep(1)

async def fun4(n: List):
    for i in n:
        await fun3([5])
        print(i)
        await asyncio.sleep(1)


async def main():
    # f = await asyncio.gather(fun1([1, 2, 3]), fun2([4, 5, 6, 7, 8, 9]), fun3([10,11,12,13]))
    await asyncio.gather(fun4([1, 2, 3]), fun3([6,7]))
    # print(f)


# asyncio.as_completed()
asyncio.run(main())

async def f():
    print('Dl 10 links')
    # await asyncio.sleep(2)

async def g():
    print('dl 5 links!')
    await f()
    # await asyncio.create_task(f())
    # task = asyncio.create_task(f())



async def h():
    # await g()
    task = asyncio.create_task(f())
    # await g()
    print('Save me')

# asyncio.run(h(), debug=True)


def fun3(n):
    while n > 0:
        yield n
        n = n-1

# f3 = fun3(5)
# print(f3.send(None))
# print(next(f3))











