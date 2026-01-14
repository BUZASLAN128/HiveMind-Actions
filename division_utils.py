import sys

def divide_by_zero():
    """
    This function attempts to divide by zero and catches the resulting error.
    """
    try:
        result = 1 / 0
    except ZeroDivisionError:
        print('Division by zero attempted!', file=sys.stderr)
