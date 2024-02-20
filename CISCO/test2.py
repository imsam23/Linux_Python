import os
import psutil
import sys

def get_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()

    return {
        'virtual_memory': psutil.virtual_memory(),
        'resident_set_size': mem_info.rss,
        'peak_memory': mem_info.peak_wset,
        'total_memory': psutil.virtual_memory().total,
        'python_memory': sys.getsizeof({}),  # Placeholder for Python-specific memory usage
    }

if __name__ == "__main__":
    # Example usage
    print(get_memory_usage())

def fun():
    for i in range(10):
        yield i
    print(get_memory_usage())

l = []
x = fun()
l.append(x)
print(l)
