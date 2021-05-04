import random

from tests import *


random.seed(20)
for key, val in globals().items():
    if key.startswith('test') and callable(val): val()