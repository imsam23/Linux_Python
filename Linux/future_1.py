import asyncio

async def my_coroutine():
    await asyncio.sleep(1)
    return 1


async def main():
    # Create a Future
    future = asyncio.Future()

    # Schedule the coroutine to be run
    asyncio.create_task(my_coroutine())

    # Wait for the Future to be completed
    result = await future

    # Print the result
    print(result)
asyncio.run(main())
