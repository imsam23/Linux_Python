import asyncio
from typing import TypeVar, Callable, AnyStr, Optional, Dict, List, Union, Mapping, Any, Awaitable
async def get_result(awaitable: Awaitable) -> str:
    try:
        result = await awaitable
    except Exception as e:
        print(f'oops!! {e}')
        return 'No result'
    else:
        return result


loop = asyncio.get_event_loop()
f = loop.create_future()
loop.call_later(3, f.set_result, "This is my result")
print(loop.run_until_complete(get_result(f)))
print(loop.run_until_complete(asyncio.gather(get_result(f), get_result(f), get_result(f))))


def callback(fut: asyncio.Future) -> None:
    print("called by", fut)


#
# async def main():
#     f = asyncio.Future()
#     loop = asyncio.get_event_loop()
#     loop.call_later(10, f.set_result, "This is my result")
#     asyncio.run(get_result(f))


