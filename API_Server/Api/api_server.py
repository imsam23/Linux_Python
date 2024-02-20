"""
https://aiohttp-middlewares.readthedocs.io/en/stable/usage.html#error-middleware
"""
import sys
import time

import aiohttp
import asyncio
import logging
from typing import List, Tuple, Callable, Awaitable, Optional
from http import HTTPStatus
from aiohttp import web
from aiohttp.web import Application, Request, Response, json_response
from aiohttp_middlewares import cors_middleware, error_middleware, timeout_middleware

"""
async def health(request):
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
                        content_type='text/html')
"""

ApiHandler = Callable[['ApiServer', 'Request'], Awaitable[Response]]
Preconditions = List[Tuple[str, type]]


class MissingParamsError(web.HTTPBadRequest):
    def __init__(self, message='Missing required route parameters'):
        super().__init__(text=message)


def requires_auth(handler: ApiHandler):
    async def wrapper(self: 'ApiServer', request: Request) -> Response:
        if not self._service_up:
            return json_response(
                status=503,
                data='Service unavailable'
            )
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer'):
            # raise web.HTTPUnauthorized()
            return json_response(
                status=401,
                data='Authorization token not found'
            )
        provided_token = auth_header.split(' ')[1]
        if provided_token != 'token':
            # raise web.HTTPForbidden
            return json_response(
                status=403,
                data='Authorization token not found'
            )
        return await handler(request)

    return wrapper


def pre_condition(
        match_info: Optional[Preconditions] = None,
        query_params: Optional[Preconditions] = None
) -> Callable[[ApiHandler], ApiHandler]:
    def decorator(handler: ApiHandler) -> ApiHandler:
        async def wrapper(self: 'ApiServer', request: Request) -> Response:
            nonlocal match_info
            match_info = match_info or []
            for match_name, match_type in match_info:
                if match_name not in request.match_info:
                    # raise MissingParamsError
                    return json_response(
                        status=400,
                        data=f'Bad request. Expect type of field {match_name} as {match_type}'
                    )
            nonlocal query_params
            query_params = query_params or []
            for param_name, param_type in query_params:
                if param_name not in request.query:
                    # raise MissingParamsError
                    return json_response(
                        status=400,
                        data=f'Bad request. Expect type of field {param_name} as {param_type}'
                    )
                try:
                    param_type(request.query[param_name])
                except Exception as e:  # noqa
                    return json_response(
                        status=400,
                        data=f'Bad request. expected query parameter type of field {param_name} as {param_type}'
                    )
            return await handler(self, request)

        return wrapper

    return decorator


class ApiServer:
    def __init__(self):
        self.request_timestamp = {}
        self._logger = logging.getLogger('ApiServer')
        self._address: str = '127.0.0.1'
        self._port: int = 8080
        self._enable_auth = 'ENABLE_AUTH'
        self._request_count = {}
        self._app = Application(logger=self._logger)
        self._app.middlewares.append(self.api_stats)
        self._app.middlewares.append(self.requires_auth_header)
        self._app.middlewares.append(self.rate_limit_middleware)
        self._service_up = True

    @web.middleware
    async def api_stats(self, request: Request, handler) -> Response:
        route = request.path
        self._request_count[route] = self._request_count.get(route, 0) + 1
        return await handler(request)

    @web.middleware
    async def requires_auth_header(self, request: Request, handler) -> Response:
        auth_header = request.headers.get('Authorization')
        if self._enable_auth and not auth_header:
            # raise web.HTTPUnauthorized()
            return json_response(
                status=400,
                data='Missing Bearer token'
            )
        return await handler(request)

    @web.middleware
    async def rate_limit_middleware(self, request: Request, handler) -> Response:
        max_request = 5
        time_window = 60

        client_ip = request.remote
        timestamp = time.time()

        if client_ip not in self.request_timestamp:
            self.request_timestamp[client_ip] = []
        client_requests = self.request_timestamp[client_ip]
        client_requests = [ts for ts in client_requests if timestamp - ts < time_window]

        if len(client_requests) >= max_request:
            return json_response(
                status=HTTPStatus.TOO_MANY_REQUESTS,
                data='Too many requests. Rate Limit exceeded'
            )
        client_requests.append(timestamp)
        self.request_timestamp[client_ip] = client_requests
        return await handler(request)

    @requires_auth
    async def stats(self, request: Request) -> Response:
        return json_response(
            status=200,
            data={
                'requests': self._request_count,
                'total': sum(self._request_count.values())
            }
        )

    @pre_condition(query_params=[('action', str)])
    async def toggle_service(self, request: Request) -> Response:
        action = request.query['action']
        action_map = {'up': True, 'down': False}
        if value := action_map.get(action) is not None:
            self._service_up = value
            return json_response(
                status=200,
                data=f'Service action updated'
            )
        else:
            return json_response(status=400, data=f'Action can be any one of these {action_map.keys()}')

    async def status_code(self):
        pass

    def _register_routes(self):
        routes_get = [
            ('/utils/stats', self.stats)]
        routes_put = [
            ('/utils/service_action', self.toggle_service)
        ]
        routes_post = []
        routes_get = [web.get(path=path, handler=handler) for path, handler in routes_get]
        routes_put = [web.put(path=path, handler=handler) for path, handler in routes_put]
        routes_post = [web.post(path=path, handler=handler) for path, handler in routes_post]
        routes = routes_get + routes_put + routes_post
        self._app.add_routes(routes)

    def run(self):
        web.run_app(app=self._app, host=self._address, port=self._port)


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        filemode='a', level=logging.DEBUG,
        format='%(levelname)s | %(message)s',
        datefmt='%Y-%m-%d,%H:%M:%S'
    )
    api_server = ApiServer()
    api_server.run()






