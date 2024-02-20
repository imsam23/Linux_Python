import mmap

"""
The mmap module can be used to improve the performance of applications that need to access large files. 
By mapping a file into memory, applications can avoid the overhead of reading the file from disk each time they need to access it.
"""

# Open the file to map.
with open("Linux_ch2_doc", "rb") as f:
  # Create a memory mapping.
  # here length is 0 which means the entire file will be mapped
  mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

  # Access the memory mapping as a byte array.
  print(mm[0:10])

  # Close the memory mapping.
  mm.close()