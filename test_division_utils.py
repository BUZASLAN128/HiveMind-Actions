import pytest
from division_utils import divide_by_zero

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide_by_zero()
