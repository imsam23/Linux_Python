import os
from abc import ABC, abstractmethod
from typing import Any, List, Tuple

import asyncpg

# Tables to be created at the start of the server
# Create users table
CREATE_USER_TABLE = \
"""
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

# Create stocks table
CREATE_STOCK_TABLE = \
"""
    CREATE TABLE IF NOT EXISTS stocks (
        stock_id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) UNIQUE NOT NULL,
        company_name VARCHAR(255) NOT NULL,
        current_price DECIMAL(12, 2),
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

# Create user_stocks table (Junction Table)
CREATE_USER_STOCK_TABLE = \
"""
    CREATE TABLE IF NOT EXISTS user_stocks (
        user_id INTEGER REFERENCES users(user_id),
        stock_id INTEGER REFERENCES stocks(stock_id),
        PRIMARY KEY (user_id, stock_id)
    )
"""

class DatabaseContextMixin:
    def __init__(self, host=None, port=None, db_name=None, user=None, password=None):
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or os.getenv('DB_PORT', 5432)
        self.database = db_name or os.getenv('DB_NAME', 'postgres')
        self.user = user or os.getenv('DB_USER_NAME', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', 'admin')
        self.dsn = self.construct_dsn()
        self.pool = None

    def construct_dsn(self):
        raise NotImplementedError("Subclasses must implement construct_dsn method")

    async def connect(self):
        raise NotImplementedError("Subclasses must implement connect method")

    async def disconnect(self):
        if hasattr(self, 'pool') and self.pool:
            await self.pool.close()

    async def execute_query(self, query: str, *args) -> Any:
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def execute_transaction(self, queries: List[Tuple]) -> Any:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                results = []
                for query, args in queries:
                    result = await connection.fetch(query, *args)
                    results.append(result)
                return results

    async def initialize_database(self):
        await self.connect()
        await self.create_tables()
        await self.disconnect()

    async def create_tables(self):
        raise NotImplementedError("Subclasses must implement create_tables method")


class PostgreSQLDatabaseContext(DatabaseContextMixin):
    async def construct_dsn(self):
        return f"postgres://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=self.dsn)

    async def create_tables(self):
        statements = [CREATE_USER_TABLE,
                      CREATE_STOCK_TABLE,
                      CREATE_USER_STOCK_TABLE]
        for statement in statements:
            await self.execute_query(statement)


class MySQLDatabaseContext(DatabaseContextMixin):
    def construct_dsn(self):
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    async def connect(self):
        raise NotImplementedError("Not implemented")

    async def create_tables(self):
        raise NotImplementedError("Not implemented create_tables method")



# async def initialize_database():
#     # Connect to the database
#     conn = await asyncpg.connect(db_type)
#
#     try:
#         # Create users table
#         CREATE_USER_TABLE = \
#         """
#             CREATE TABLE IF NOT EXISTS users (
#                 user_id SERIAL PRIMARY KEY,
#                 username VARCHAR(50) UNIQUE NOT NULL,
#                 email VARCHAR(100) UNIQUE NOT NULL,
#                 password_hash VARCHAR(100) NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         """
#
#         # Create stocks table
#         CREATE_STOCK_TABLE = \
#         """
#             CREATE TABLE IF NOT EXISTS stocks (
#                 stock_id SERIAL PRIMARY KEY,
#                 symbol VARCHAR(20) UNIQUE NOT NULL,
#                 company_name VARCHAR(255) NOT NULL,
#                 current_price DECIMAL(12, 2),
#                 last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         """
#
#         # Create user_stocks table (Junction Table)
#         CREATE_USER_STOCK_TABLE = \
#         """
#             CREATE TABLE IF NOT EXISTS user_stocks (
#                 user_id INTEGER REFERENCES users(user_id),
#                 stock_id INTEGER REFERENCES stocks(stock_id),
#                 PRIMARY KEY (user_id, stock_id)
#             )
#         """
#         statements = [CREATE_USER_TABLE,
#                       CREATE_STOCK_TABLE,
#                       CREATE_USER_STOCK_TABLE]
#         for statement in statements:
#             status = await conn.execute(statement)
#             print(status)
#     finally:
#         # Close the database connection
#         await conn.close()
#
"""
async def example_usage():
    # Using PostgreSQL
    postgres_db = PostgreSQLDatabaseContext()
    await postgres_db.initialize_database()
    result = await postgres_db.execute_query("SELECT * FROM table_name")
    print("PostgreSQL result:", result)
    await postgres_db.disconnect()

    # Using MySQL
    mysql_db = MySQLDatabaseContext()
    await mysql_db.initialize_database()
    result = await mysql_db.execute_query("SELECT * FROM table_name")
    print("MySQL result:", result)
    await mysql_db.disconnect()

# Running the example
asyncio.run(example_usage())
"""