import math
import numpy as np
from decimal import Decimal
from backend.services.serialization import serialize_value

def test_serialize_decimal():
    assert serialize_value(Decimal("59.41")) == 59.41
    assert serialize_value(Decimal("99999.57")) == 99999.57

def test_serialize_numpy():
    assert serialize_value(np.float64(3.14)) == 3.14
    assert serialize_value(np.int64(42)) == 42
    assert isinstance(serialize_value(np.int64(42)), int)
    assert isinstance(serialize_value(np.float64(3.14)), float)

def test_serialize_nan_inf():
    assert serialize_value(float("nan")) is None
    assert serialize_value(np.nan) is None
    assert serialize_value(float("inf")) is None
    assert serialize_value(float("-inf")) is None

def test_serialize_none():
    assert serialize_value(None) is None

def test_serialize_nested():
    data = {
        "cost": Decimal("10.5"),
        "list": [np.nan, 5, Decimal("3.2")],
        "nested": {"val": float("inf")}
    }
    expected = {
        "cost": 10.5,
        "list": [None, 5, 3.2],
        "nested": {"val": None}
    }
    assert serialize_value(data) == expected
