import asyncio
import logging
import sys
from typing import Dict

import websockets
from authentication import AuthenticationManager,TokenAuth
logger = logging.getLogger(__name__)
logging.basicConfig()

CLOSE_STATUS_NORMAL = ''
DEFAULT_CLOSE_REASON = ''


class API:

    async def run_forever(self):
        print('Start WebSocket Server')
        await self._run_forever()

    async def new_client(self, client, server):
        pass

    async def client_left(self, client, server):
        pass

    # async def message_received(self, client, server, message):
    #     pass
    #
    # async def set_fn_new_client(self, fn):
    #     self.new_client = fn
    #
    # async def set_fn_client_left(self, fn):
    #     self.client_left = fn
    #
    # async def set_fn_message_received(self, fn):
    #     self.message_received = fn

    async def send_message(self, client, msg):
        self._unicast(client, msg)

    async def send_message_to_all(self, msg):
        self._multicast(msg)

    async def deny_new_connections(self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON):
        self._deny_new_connections(status, reason)

    async def allow_new_connections(self):
        self._allow_new_connections()

    async def shutdown_gracefully(self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON):
        self._shutdown_gracefully(status, reason)

    async def shutdown_abruptly(self):
        self._shutdown_abruptly()

    async def disconnect_clients_gracefully(self, status=CLOSE_STATUS_NORMAL, reason=DEFAULT_CLOSE_REASON):
        self._disconnect_clients_gracefully(status, reason)

    async def disconnect_clients_abruptly(self):
        self._disconnect_clients_abruptly()


class WebSocketServer(API):
    """
	A websocket server waiting for clients to connect.

    Args:
        port(int): Port to bind to
        host(str): Hostname or IP to listen for connections. By default 127.0.0.1
            is being used. To accept connections from any client, you should use
            0.0.0.0.
        loglevel: Logging level from logging module to use for logging. By default
            warnings and errors are being logged.

    Properties:
        clients(list): A list of connected clients. A client is a dictionary
            like below.
                {
                 'id'      : id,
                 'handler' : handler,
                 'address' : (addr, port)
                }
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 8081, loglevel: int = logging.WARNING, key=None, cert=None):
        logger.setLevel(loglevel)
        self.host = host
        self.port = port
        self.cert = cert
        self.key = key
        self.clients = []
        # self.loop = loop
        # self.stop = self.loop.create_future()
        self.stop = asyncio.Event()
        self._deny_client = False
        self.client_mgr = ClientManager()
        self.msg_handler = MessageHandler()
        self.handler = ConnectionHandler(self.client_mgr, self.msg_handler)
        # self.process_request = process_request

    async def _run_forever(self):
        # cls_name = self.__class__.__name__
        try:
            print(f"Listening on port {self.port} for client..")
            async with websockets.serve(self.handler.handle_connection, self.host, self.port, process_request=self._process_request):
                # await self.stop
                await self.stop.wait()
        except KeyboardInterrupt:
            # close the server
            print(f'Server Terminated')
        except Exception as e:
            # cleanup()
            logger.error(str(e), exc_info=True)
            sys.exit(1)

    async def _process_request(self, request_headers, path):
        print('Authenticating User')
        auth_manager = AuthenticationManager()
        # auth_manager.set_strategy(TokenAuth)
        if auth_manager.authenticate(request_headers):
            print('Authenticating User done')
        else:
            print('Authenticating User failed')

    async def _terminate_client_handler(self, handler):
        pass

    async def _terminate_client_handlers(self):
        pass

    async def _shutdown_gracefully(self, status='close_status_normal', reason='default_close_reason'):
        pass

    async def _shutdown_abruptly(self):
        pass

    async def _disconnect_gracefully(self, status='close_status_normal', reason='default_close_reason'):
        pass

    async def _disconnect_abruptly(self, status='close_status_normal', reason='default_close_reason'):
        pass


# class ConnectionManager:
#     async def _allow_new_connection(self):
#         pass
#
#     async def _deny_new_connection(self, status, reason):
#         pass


class ClientManager:
    def __init__(self):
        self.clients: Dict = {}

    async def register_new_client(self, client):
        # Add entry to DB
        pass

    async def deregister_client(self, client):
        # remove entry from DB
        pass

    async def add_client(self, client):
        client_id = ''
        client_info = {}
        self.clients[client_id] = client_info
        logging.info(f'Added client: {client_id}')

    async def remove_client(self, client):
        client_id = client
        if client_id in self.clients:
            self.clients.pop(client_id)
            logging.info(f'Removed client: {client_id}')
        logging.info(f'client not found: {client_id}')

    async def client_exists(self, client_id):
        return client_id in self.clients



class MessageHandler:
    async def handle_message(self, websocket, message):
        # TODO do some data handling here
        try:
            """
            Register new client to DB
            add client to client list
            remove client from client list
            deregister existing client
            
            Expecting subscription data in the form of {'subscriptions': [stk1, stk2, stk3]}
             """
            # Message to check
            data = message.get('subscriptions')
            if data:
                # store it in in db
                await self.send_data(message)
                pass
            else:
                print(f'Not saving data into DB  ')
        except Exception as e:
            pass

    async def send_data(self, websocket, data):
        try:
            await websocket.send(data)
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error('Could not send data to client. Connection ' \
                         f'closed. exception = {e}')
        except Exception as e:
            logger.error('Exception occured while sending data to client.' \
                         f' exception = {e}')


class ConnectionHandler:
    def __init__(self, client_mgr, message_handler):
        self.client_mgr = client_mgr
        self.msg_handler = message_handler

    async def _allow_new_connection(self):
        pass

    async def _deny_new_connection(self, status, reason):
        pass

    async def handle_connection(self, websocket, path):
        """
        step 1: First Authenticate
        step 2: Check if connection is allowed or not
        step 3: Handle the message
                check for the valid message


        """
        # check if connection is new then check if it is allowed
        # If it is allowed then update it in connection list
        caddr = websocket.remote_address[0]
        print(caddr)
        # TODO: Need to do authentication
        try:
            async for message in websocket:
                print(message)
                await self.msg_handler.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosedError as e:
            print(f'{caddr} is disconnect from {caddr}')
            logger.error(f'{caddr} is disconnect from {caddr}')
        except websockets.exceptions.ConnectionClosed as e:
            print(f'{caddr} is disconnect from {caddr}')
        except Exception as e:
            logger.error(f'Exception occurred in the connection from'
                         f'{caddr} to {caddr} '
                         f'exception = {e}')



# async def main():
#     loop = asyncio.get_event_loop()
#     ws_server = WebSocketServer(loop=loop)
#     asyncio.run(ws_server.run_forever())


if __name__ == "__main__":
    ws_server = WebSocketServer()
    asyncio.run(ws_server.run_forever())

# TODO:
# Need to implement Client side code
#  Need to implement Authtentication class
#  WebSocketHandler class
# Need to implement Database connectivity
# Need to do 
