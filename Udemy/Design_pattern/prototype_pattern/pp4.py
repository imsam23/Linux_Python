import copy

# Prototype (Common Interface)
class DatabaseConnectionPrototype:
    def clone(self):
        pass

    def execute_query(self, query):
        pass

    def close(self):
        pass

# Concrete Prototype: Database Connection
class DatabaseConnection(DatabaseConnectionPrototype):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.is_open = False

    def clone(self):
        return copy.copy(self)

    def execute_query(self, query):
        if self.is_open:
            print(f"Executing query '{query}' using connection: {self.connection_string}")
        else:
            print("Connection is closed. Cannot execute query.")

    def open(self):
        self.is_open = True
        print(f"Connection opened: {self.connection_string}")

    def close(self):
        self.is_open = False
        print(f"Connection closed: {self.connection_string}")

# Object Pool
class ObjectPool:
    def __init__(self, prototype, pool_size):
        self.prototype = prototype
        self.pool_size = pool_size
        self.object_pool = [self.prototype.clone() for _ in range(pool_size)]

    def acquire(self):
        if self.object_pool:
            return self.object_pool.pop()
        else:
            print("Object pool is empty. Cannot acquire a connection.")
            return None

    def release(self, connection):
        if len(self.object_pool) < self.pool_size:
            connection.close()
            self.object_pool.append(connection)
        else:
            print("Object pool is full. Cannot release the connection.")

# Client Code
connection_prototype = DatabaseConnectionPrototype()
db_pool = ObjectPool(connection_prototype, pool_size=3)

# Acquire and use connections
connection1 = db_pool.acquire()
connection2 = db_pool.acquire()

if connection1 and connection2:
    connection1.open()
    connection1.execute_query("SELECT * FROM users")

    connection2.open()
    connection2.execute_query("UPDATE orders SET status='shipped'")

    db_pool.release(connection1)
    db_pool.release(connection2)

# Attempt to acquire a connection when the pool is empty
empty_pool_connection = db_pool.acquire()
# Output: Object pool is empty. Cannot acquire a connection.

# Attempt to release a connection when the pool is full
db_pool.release(connection1)
# Output: Object pool is full. Cannot release the connection.
