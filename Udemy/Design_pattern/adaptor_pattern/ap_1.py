"""
Use case:
  Suppose you have a system that works with various data sources,
  such as a file system, a database, and an external API.
  Each of these data sources may have its own interface for reading data.
  However, you want to provide a unified interface in your system so that
  you can easily switch between these data sources without changing the core logic of your application.
"""


# Common interface for all data source adapters
class DataSourceAdapter:
    def read_data(self):
        pass


# Adapter for reading data from a file system
class FileSystemAdapter(DataSourceAdapter):
    def read_data(self):
        print("Reading data from file system...")


# Adapter for accessing data from a database
class DatabaseAdapter(DataSourceAdapter):
    def read_data(self):
        print("Reading data from database...")


# Adapter for fetching data from an external API
class APIAdapter(DataSourceAdapter):
    def read_data(self):
        print("Fetching data from external API...")


# Client code that uses the common interface
class DataProcessor:
    def __init__(self, adapter):
        self.adapter = adapter

    def process_data(self):
        self.adapter.read_data()
        # Additional processing logic can be added here


# Usage
file_system_adapter = FileSystemAdapter()
database_adapter = DatabaseAdapter()
api_adapter = APIAdapter()

data_processor_1 = DataProcessor(file_system_adapter)
data_processor_1.process_data()

data_processor_2 = DataProcessor(database_adapter)
data_processor_2.process_data()

data_processor_3 = DataProcessor(api_adapter)
data_processor_3.process_data()
