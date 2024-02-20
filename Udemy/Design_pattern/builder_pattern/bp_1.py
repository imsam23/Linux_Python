class Computer:
    def __init__(self, cpu, memory, storage, gpu=None):
        self.cpu = cpu
        self.memory = memory
        self.storage = storage
        self.gpu = gpu

    def __str__(self):
        gpu_info = f' with {self.gpu}' if self.gpu else ''
        return f'Computer: CPU={self.cpu}, Memory={self.memory}, Storage={self.storage}{gpu_info}'


class ComputerBuilder:
    def __init__(self, cpu, memory, storage):
        self.computer = Computer(cpu, memory, storage)

    def add_gpu(self, gpu):
        self.computer.gpu = gpu
        return self

    def build(self):
        return self.computer


# Usage
builder = ComputerBuilder(cpu="Intel i9", memory="32GB", storage="1TB SSD")
computer = builder.add_gpu("NVIDIA RTX 3080").build()

print(computer)  # Outputs: Computer: CPU=Intel i9, Memory=32GB, Storage=1TB SSD with NVIDIA RTX 3080
