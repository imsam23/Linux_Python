from queue import Queue

"""
Managing Object Lifecycles:
Example: Object pools for database connections, thread pool management.
"""


# Product: Database Connection
class DatabaseConnection:
    def execute_query(self, query):
        pass

    def close(self):
        pass


# Concrete Product: MySQL Database Connection
class MySQLConnection(DatabaseConnection):
    def execute_query(self, query):
        print(f"MySQL executing query: {query}")

    def close(self):
        print("Closing MySQL connection")


# Concrete Product: PostgreSQL Database Connection
class PostgreSQLConnection(DatabaseConnection):
    def execute_query(self, query):
        print(f"PostgreSQL executing query: {query}")

    def close(self):
        print("Closing PostgreSQL connection")


# Creator (Factory): Database Connection Factory
class DatabaseConnectionFactory:
    def create_connection(self):
        pass


# Concrete Creator (Factory): MySQL Connection Factory
class MySQLConnectionFactory(DatabaseConnectionFactory):
    def create_connection(self):
        return MySQLConnection()


# Concrete Creator (Factory): PostgreSQL Connection Factory
class PostgreSQLConnectionFactory(DatabaseConnectionFactory):
    def create_connection(self):
        return PostgreSQLConnection()


# Object Pool
class ConnectionPool:
    def __init__(self, factory, max_connections):
        self.factory = factory
        self.max_connections = max_connections
        self.connection_pool = Queue()

    def get_connection(self):
        if not self.connection_pool.full():
            connection = self.factory.create_connection()
            self.connection_pool.put(connection)
            return connection
        else:
            print("Connection pool is full. Cannot get a new connection.")

    def release_connection(self, connection):
        if not self.connection_pool.empty():
            self.connection_pool.put(connection)
        else:
            print("Connection pool is empty. Cannot release connection.")


# Client Code
def perform_database_operations(connection_pool, query):
    connection = connection_pool.get_connection()
    connection.execute_query(query)
    connection_pool.release_connection(connection)


# Example Usage
mysql_connection_factory = MySQLConnectionFactory()
postgres_connection_factory = PostgreSQLConnectionFactory()

mysql_connection_pool = ConnectionPool(mysql_connection_factory, max_connections=5)
postgres_connection_pool = ConnectionPool(postgres_connection_factory, max_connections=3)

perform_database_operations(mysql_connection_pool, "SELECT * FROM users")
perform_database_operations(postgres_connection_pool, "INSERT INTO orders VALUES (...)")

# Closing connections in a real-world scenario would be done appropriately, here it's simplified for demonstration.
