"""
asynchronously how to generate only one token using asyncio.get_running_loop().create_future()
for the multiple requests when token expires
"""

import asyncio
import time

# Simulated token
token = None

# Lock for token generation
token_lock = asyncio.Lock()

# Function to simulate token generation
async def generate_token():
    # Simulating token generation delay
    await asyncio.sleep(2)
    return f"Token"

# Function to check token expiration and generate a new token if needed
async def get_token():
    global token
    if token is None or is_token_expired(token):
        async with token_lock:
            if token is None or is_token_expired(token):
                token_task = asyncio.get_running_loop().create_future()
                if token is None:
                    token_task.set_result(await generate_token())
                else:
                    await token_task
                token = token_task.result()
    return token

# Function to simulate token expiration check
def is_token_expired(token):
    # Simulating token expiration
    return time.time() % 5 == 0

# Function to simulate requests using the token
async def make_request(user):
    # Retrieve the token
    token = await get_token()

    # Process the request using the token
    print(f"Request processed for user {user} using token: {token}")

# List of users making requests
users = ["user1", "user2", "user3", "user4"]

# Create and run the event loop
async def main():
    tasks = [make_request(user) for user in users]
    await asyncio.gather(*tasks)

# Run the event loop
asyncio.run(main())
