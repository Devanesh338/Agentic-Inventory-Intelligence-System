import numpy as np
from decimal import Decimal
import math
from typing import Any, Dict, List

def serialize_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (np.int64, np.int32, np.int16, np.int8)):
        return int(val)
    if isinstance(val, (np.float64, np.float32, np.float16)):
        val = float(val)
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if isinstance(val, dict):
        return {str(k): serialize_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [serialize_value(v) for v in val]
    if isinstance(val, tuple):
        return [serialize_value(v) for v in val]
    return val

def make_canonical(data: Dict[str, Any]) -> Dict[str, Any]:
    return serialize_value(data)
