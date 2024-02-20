"""
Links to read:
https://ably.com/blog/websocket-authentication
https://websockets.readthedocs.io/en/stable/topics/authentication.html

The WebSocket specification does not prescribe any particular way to authenticate a WebSocket connection once
it’s established but suggests you authenticate the HTTP handshake before establishing the connection:



"""
# def generate_token(user_name, email):
#     # add_data_to_toke
#     pass
#
# def auth(credentials):
#     user_name = credentials.get('user_name')
#     email = credentials.get('email')
#     token = generate_token(user_name, email)
#     return token
import jwt

SECRET_KEY = 'SERCRET_KEY_HERE'


class AuthStrategy:
    def authenticate(self, credentials):
        raise NotImplementedError("This method must be implemented in subclasses")


class UsernamePasswordAuth(AuthStrategy):
    def authenticate(self, credentials):
        # username, password = credentials
        # Implement actual username/password authentication logic here
        # ...
        return True  # Replace with actual authentication result


class TokenAuth(AuthStrategy):
    def authenticate(self, credentials):
        request_headers = credentials
        if 'Authorization' not in request_headers:
            return False
        auth_header = request_headers['Authorization'].decode()
        auth_type, jwt_token = auth_header.split(' ')
        if auth_type.lower() != 'bearer':
            return False
        try:
            decoded_token = jwt.decode(jwt_token, SECRET_KEY, algorithms=['HS256'])
            # TODO: Perform additional check here
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
        return True


class AuthenticationManager:
    def __init__(self, default_strategy=UsernamePasswordAuth()):
        self.strategy = default_strategy

    def set_strategy(self, strategy):
        self.strategy = strategy

    def authenticate(self, credentials):
        return self.strategy.authenticate(credentials)

if __name__ == 'main':
    # Usage example
    auth_manager = AuthenticationManager()

    # Username/password authentication
    if auth_manager.authenticate(("user", "password")):
        print("Username/password authentication successful!")

    # Token-based authentication
    auth_manager.set_strategy(TokenAuth())
    if auth_manager.authenticate("valid_token"):
        print("Token-based authentication successful!")






