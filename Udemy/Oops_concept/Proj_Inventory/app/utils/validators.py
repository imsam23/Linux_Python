"""Various Validators"""

def validate_integer(arg_name, arg_val, min_val=None, max_val=None,
                     custom_min_msg=None, custom_max_msg=None ):
    """Validates that arg_val is an integer and optionally falls within specific bound.
    A custom override error message can be provided when min/max bunds are exceeded

    Args:
        arg_name(str): the name of the argument
        arg_val(int): the valued being validated
        min_val(int): optional, specifies the min value
        max_val(int): optional, specifies the max value
        custom_min_msg(str):
        custom_max_msg(str):

    Returns:
        None: no exception raised if validation passes
    Raise:
        TypeError: if `arg_va` is not an integer
        ValueError: if `arge_val` does not satisfy the bounds.
    """

    if not isinstance(arg_val, int):
        raise TypeError(f'{arg_name} must be integer')
    if min_val is not None and arg_val < min_val:
        if custom_min_msg is not None:
            raise ValueError(custom_min_msg)
        raise ValueError(f'{arg_name} can not be less than {min_val}')

    if max_val is not None and arg_val > max_val:
        if custom_max_msg is not None:
            raise ValueError(custom_max_msg)
        raise ValueError(f'{arg_name} can not be less than {max_val}')
