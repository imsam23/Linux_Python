"""
asynchronously how to generate only one token using asyncio.get_running_loop().create_future()
for the multiple requests when token expires
"""

import concurrent.futures
import time

# Function to simulate token generation
def generate_token(user):
    # Simulating token generation delay
    time.sleep(2)
    return f"Token for {user}"

# Function to check token expiration and generate a new token if needed
def check_token(user):
    token = generate_token(user)
    if is_token_expired(token):
        token = generate_token(user)
    return token

# Function to simulate token expiration check
def is_token_expired(token):
    # Simulating token expiration
    return time.time() % 5 == 0

# List of users requesting tokens
users = ["user1", "user2", "user3", "user4"]

# Create a ThreadPoolExecutor
with concurrent.futures.ThreadPoolExecutor() as executor:
    # Submit token generation tasks to the executor and store the future objects
    futures = [executor.submit(check_token, user) for user in users]

    # Retrieve the results from the future objects as they complete
    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
            print(f"Token generated: {result}")
        except Exception as e:
            print(f"An error occurred: {e}")
