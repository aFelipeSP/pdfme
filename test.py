import random
import copy

from tests import *

random.seed(20)
globals_ = list(globals().keys())
for key in globals_:
    val = globals()[key]
    if key.startswith('test') and callable(val): val()