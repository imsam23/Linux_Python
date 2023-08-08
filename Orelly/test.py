import asyncio
import time
import concurrent.futures
from concurrent.futures import Executor
import aiohttp

from util import delay, async_timed
# from util import delay


# async def delay(n):
#     print(f'delaying for {n} secs')
#     await asyncio.sleep(n)
#     print(f'delaying for {n} secs completed')


async def main1():
    start_time = time.perf_counter()
    await delay(2)
    print('Hello')
    task = []
    task1 = asyncio.create_task(delay(3))
    print('Hello1')
    task2 = asyncio.create_task(delay(1))
    print('Hello2')
    task3 = asyncio.create_task(delay(4))
    print('Hello3')
    await task1
    print('Hello4')
    await task1
    print('Called again')
    await task2
    print('Hello5')
    await task3  # This one also get executed
    print('Hello6')

    await asyncio.gather(task3)
    end_time = time.perf_counter()
    print(f'time taken: {end_time - start_time}')

# CHAPTER 4
@async_timed()
async def main() -> None:
    delay_times = [3, 3, 3]
    [await asyncio.create_task(delay(seconds)) for seconds in delay_times]  # it will complete in 9 sec
    tasks = [asyncio.create_task(delay(seconds)) for seconds in delay_times]
    await asyncio.gather(*tasks)  # it will complete in 3 sec almost1


import functools
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from util import async_timed


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        urls = ['https:// www .example .com' for _ in range(1000)]
        tasks = [loop.run_in_executor(pool, functools.partial(get_status_code, url)) for url in urls]
        results = await asyncio.gather(*tasks)
        print(results)






if __name__ == "__main__":
    asyncio.run(main())
