"""Inventory models"""

from app.utils.validators import validate_integer


class Resource:
    """Base class for resources"""
    def __init__(self, name, manufacturer, total, allocated):
        """

        Args:
            name(str):
            manufacturer(str):
            total(int):
            allocated(int):
        Note:
            `allocated` cant exceed total
        """
        self._name = name
        self._manufacturer = manufacturer

        validate_integer('total', total, min_val=0)
        self._total = total

        validate_integer('allocated', allocated, 0, total, custom_max_msg='Allocated inventory can not exceed total '
                                                                          'inventory')
        self._allocated = allocated

    @property
    def name(self):
        """

        Returns:
            str: the resource name

        """
        return self._name

    @property
    def manufacturer(self):
        """

        Returns:
            str: the manufacturer name

        """
        return self._manufacturer

    @property
    def allocated(self):
        """

        Returns:
            int: number of resources in use
        """
        return self._allocated

    @property
    def category(self):
        """

        Returns:
            int: the resource category
        """
        return type(self).__name__.lower()

    @property
    def total(self):
        """

        Returns:
            int: number of total resource
        """
        return self._total

    @property
    def available(self):
        """

        Returns:
            int: number of resource available for use
        """
        return self.total - self.allocated

    def __str__(self):
        return self.name

    def __repr__(self):
        return (f'{self.name} ({self.category} - {self.manufacturer}): '
                f'total={self.total}, allocated={self.allocated}'
                )

    def claim(self, num):
        """
        Calin num inventory if available
        Args:
            num(int): Number of items to clain

        Returns:

        """
        validate_integer('num', num, 1, self.available,
                         custom_max_msg='Can not claim more than available')
        self._allocated += num

    def freeup(self, num):
        """
        Return an inventory item to the available pool
        Args:
            num(int): Number of items to return(can not exceed numebr in use)

        Returns:

        """
        validate_integer('num', num, 1, self.allocated,
                         custom_max_msg='Can not return more than allocated')
        self._allocated -= num

    def dies(self, num):
        """
        Number of items to deallocate and remove from the inventory pool
        Args:
            num(int): Numbe of items that have died

        Returns:

        """
        validate_integer('num', num, 1, max_val=self._allocated,
                         custom_max_msg='Cannot retire more than allocated')
        self._total -= num
        self._allocated -= num

    def purchased(self, num):
        """
        Add new inventory to the pool
        Args:
            num(int): number of items to add to the pool

        Returns:

        """
        validate_integer('num', num, 1)
        self._total += num


class CPU(Resource):
    """
    Resource subclass used to track the CPU resource inventory
    """
    def __init__(self, name, manufacture, total, allocated,
                 cores, socket, power_watts):
        """

        Args:
            name(str): resource name
            manufacture(str): resource manufacturer
            total(int): current total amount of resources
            allocated(int): current count of in-use resource
            cores(int): number of cores
            socket(str): CPU Socket type
            power_watts(int): CPU rated wattage
        """
        super().__init__(name, manufacture, total, allocated)
        validate_integer('cores', cores, 1)
        validate_integer('power_watts', power_watts, 1)
        self._cores = cores
        self._socks = socket
        self._power_watts = power_watts

    @property
    def cores(self):
        """

        Returns:

        """
        return self._cores

    @property
    def socks(self):
        """

        Returns:

        """
        return self._socks

    @property
    def power_wattage(self):
        """

        Returns:

        """
        return self._power_watts

    def __repr__(self):
        return f'{self.category}: {self.name} ({self.socks} - x{self.cores})'



