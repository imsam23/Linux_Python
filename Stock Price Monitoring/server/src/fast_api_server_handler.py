from fastapi import FastAPI

class UserRoutes(FastAPI):
    def __init__(self):
        super().__init__()

    async def get_user(self, user_id: int):
        return {'message': 'Hello World !'}
        # Logic to retrieve user data

# class ProductRoutes(FastAPI):
#     def __init__(self):
#         super().__init__()
#
#     @FastAPI.post("/products")
#     async def create_product(self, product_data: Product):
#         # Logic to create a product

# ... similar classes for other endpoint groups
