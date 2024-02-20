from typing import Type, Union
from rest_framework.authentication import BaseAuthentication, TokenAuthentication, SessionAuthentication
from rest_framework.request import Request
from rest_framework import exceptions


class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request: Request):
        # Implement your custom authentication logic here
        # Return a two-tuple of (user, auth) if authentication succeeds,
        # or None otherwise.
        return None


class AuthenticationFactory:
    def __init__(self, authentication_type: str):
        self.authentication_type = authentication_type

    def create_authentication(self) -> Type[BaseAuthentication]:
        if self.authentication_type == 'token':
            return TokenAuthentication
        elif self.authentication_type == 'session':
            return SessionAuthentication
        elif self.authentication_type == 'custom':
            return CustomAuthentication
        else:
            raise ValueError("Invalid authentication type")


# Example usage:

# Set the desired authentication type ('token', 'session', or 'custom')
authentication_type = 'custom'

# Create an instance of the AuthenticationFactory with the desired type
auth_factory = AuthenticationFactory(authentication_type)

# Create an authentication class instance using the factory
authentication_class = auth_factory.create_authentication()


# Simulate a request for demonstration purposes
class MockRequest:
    def __init__(self, authentication_type: str):
        self.auth = authentication_class()
        self.headers = {'Authorization': 'Bearer some_token'} if authentication_type == 'token' else {}


# Use the authentication class in your Django REST framework views or settings
request = MockRequest(authentication_type)
try:
    user, auth = authentication_class.authenticate(request)
    print(f"Authentication successful. User: {user}")
except exceptions.AuthenticationFailed as e:
    print(f"Authentication failed. Error: {e}")
