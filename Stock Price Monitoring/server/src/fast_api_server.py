"""
 http://127.0.0.1:8000/openapi.json

"""

from fastapi import FastAPI
from uvicorn import run
from fast_api_server_handler import UserRoutes

app = FastAPI()
class FastApiServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.app = app

    def define_routes(self):
        # Add your application routes and logic here
        # For example:
        user_routes = UserRoutes()
        app.include_router(user_routes, prefix="/users")

    def run_server(self):
        self.define_routes()  # Ensure routes are defined before running
        run("fast_api_server:app", host=self.host, port=self.port)

if __name__ == "__main__":
    app_instance = FastApiServer(host="127.0.0.1", port=8001)
    app_instance.run_server()



    # uvicorn.run("server1:app", host="127.0.0.1", port=8000, reload=True)


