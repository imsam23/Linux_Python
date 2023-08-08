from typing import List
def partition(data: List,
              chunk_size: int) -> List:
    for i in range(0, len(data), chunk_size):
        print(i)
        yield data[i:i + chunk_size]

data = ["My name is Satyam1", "My name is Satyam2", "My name is Satyam3", "My name is Satyam4",
        "My name is Satyam5", "My name is Satyam6", "My name is Satyam7", "My name is Satyam8",
        "My name is Satyam9", "My name is Satyam10", "My name is Satyam11"]

for v in partition(data, 2):
    print(v)