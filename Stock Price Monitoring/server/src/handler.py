from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

class Product(BaseModel):
    id: int
    name: str

class UserRepository:
    def get_user(self, user_id: int) -> User:
        # Logic to retrieve user data
        pass

class ProductService:
    def create_product(self, product_data: Product) -> Product:
        # Logic to create a product
        pass

def get_user_repository():
    # Logic to create and return the user repository instance
    pass

def get_product_service():
    # Logic to create and return the product service instance
    pass

user_routes = APIRouter()
product_routes = APIRouter()

@user_routes.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, user_repository: UserRepository = Depends(get_user_repository)):
    user = user_repository.get_user(user_id)
    return user

@product_routes.post("/products", response_model=Product)
async def create_product(product_data: Product, product_service: ProductService = Depends(get_product_service)):
    product = product_service.create_product(product_data)
    return product

app = FastAPI()
app.include_router(user_routes)
app.include_router(product_routes)
