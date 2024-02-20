# import asyncio
# from typing import TypeVar, Callable, AnyStr, Optional, Dict, List, Union, Mapping, Any, Awaitable
# async def get_result(awaitable: Awaitable) -> str:
#     try:
#         result = await awaitable
#     except Exception as e:
#         print(f'oops!! {e}')
#         return 'No result'
#     else:
#         return result
#
#
# loop = asyncio.get_event_loop()
# f = loop.create_future()
# loop.call_later(3, f.set_result, "This is my result")
# print(loop.run_until_complete(get_result(f)))
# print(loop.run_until_complete(asyncio.gather(get_result(f), get_result(f), get_result(f))))
import asyncio

from resource import *


def get_memory_usage():
    # Get memory usage in bytes
    memory_usage_bytes = getrusage(RUSAGE_SELF).ru_maxrss
    # Convert to MB
    memory_usage_mb = memory_usage_bytes / (1024.0 * 1024.0)
    return memory_usage_mb

{
"category_name": ["umbrella APP RULE 52"]
}
def post(self, uri_ctx):

    # Get memory usage before running the post method
    initial_memory_usage = get_memory_usage()

    # Your existing post method code goes here

    # Get memory usage after running the post method
    final_memory_usage = get_memory_usage()

    # Calculate memory usage increase
    memory_increase = final_memory_usage - initial_memory_usage

    print("Memory usage increased by {:.2f} MB".format(memory_increase))


a = [3, 4, 6 ,12, 11, 1, 0]
# [0,1,3,4,6,11,12]

def solve(prices: list[int]) -> int:
    initial_memory_usage = get_memory_usage()
    max_profit = 0
    for i, v in enumerate(prices):
        for j,k in enumerate(prices):
            if i < j and k-v > max_profit:
                max_profit = k-v
    final_memory_usage = get_memory_usage()
    memory_increase = final_memory_usage - initial_memory_usage
    print("Memory usage increased by {:.2f} MB".format(memory_increase))
    return max_profit

print(solve(a))
async def invoke():
    print('Hello')
    await invoke()


# asyncio.run(invoke())

def callback(fut: asyncio.Future) -> None:
    print("called by", fut)


#
# async def main():
#     f = asyncio.Future()
#     loop = asyncio.get_event_loop()
#     loop.call_later(10, f.set_result, "This is my result")
#     asyncio.run(get_result(f))


