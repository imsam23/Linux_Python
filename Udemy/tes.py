import asyncio
import time
from asyncio import CancelledError, Future


async def delay(n):
    print(f'Delaying for {n} seconds')
    await asyncio.sleep(n)
    print(f'Waited {n} seconds')


async def test1():
    task1 = asyncio.create_task(delay(3))
    print(f'Taske created is {task1}')
    await task1

async def test2():
    task1 = asyncio.create_task(delay(3))
    print(f'Taske created is task1 {task1}')
    task2 = asyncio.create_task(delay(2))
    print(f'Taske created is task2 {task2}')
    task3 = asyncio.create_task(delay(3))
    print(f'Taske created is task3 {task3}')
    await task1
    await task2
    await task3

# def main():
#     print(f'name: {__name__}')
#     # asyncio.run(test1())
#     asyncio.run(test2())


async def hello_every_second():
    for i in range(2):
        await asyncio.sleep(1)
        print("I'm running other code while I'm waiting!")


async def main1():
    first_delay = asyncio.create_task(delay(3))
    second_delay = asyncio.create_task(delay(3))
    await hello_every_second()
    await first_delay
    await second_delay


async def main2():
    long_task = asyncio.create_task(delay(4))

    seconds_elapsed = 0

    while not long_task.done():
        print('Task not finished, checking again in a second.')
        # time.sleep(1)
        await asyncio.sleep(1)
        seconds_elapsed = seconds_elapsed + 1
        print(seconds_elapsed)
        if seconds_elapsed == 5:
            long_task.cancel()

    try:
        await long_task
    except CancelledError:
        print('Our task was cancelled')


def make_request() -> Future:
    future = Future()
    asyncio.create_task(set_future_value(future))
    return future


async def set_future_value(future) -> None:
    await asyncio.sleep(1)
    future.set_result(42)


async def main():
    future = make_request()
    print(f'Is the future done? {future.done()}')
    value = await future
    print(f'Is the future done? {future.done()}')
    print(value)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
