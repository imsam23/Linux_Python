import asyncio
import time
import aiohttp
from aiohttp import ClientSession


"""
CONNECTION POOLING:
With a session, you’ll keep many connections open, which can then be recycled. This is known as connection 
pooling. Connection pooling is an important concept that aids the performance of our aiohttp-based applications. 
Since creating connections is resource intensive, creating a reusable pool of them cuts down on resource allocation 
costs. A session will also internally save any cookies that we receive, although this functionality can be turned off 
if desired. 

Note that a ClientSession will create a default maximum of 100 connections by default, providing an implicit upper 
limit to the number of concurrent requests we can make. To change this limit, we can create an instance of an aiohttp 
TCPConnector specifying the maximum number of connections and passing that to the ClientSession 

CONNECTION POOLING
"""

# from util import async_timed


# @async_timed()
async def fetch_status(session: ClientSession, url: str) -> int:
    async with session.get(url) as result:
        return result.status


# @async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        url = 'https://www.example.com'
        status = await fetch_status(session, url)
        print(f'Status for {url} was {status}')


asyncio.run(main())