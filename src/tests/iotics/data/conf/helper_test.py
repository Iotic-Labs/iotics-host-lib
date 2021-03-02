import contextlib
import os
from copy import deepcopy
from typing import Dict


@contextlib.contextmanager
def set_env(variables: Dict[str, str]):
    saved_env = deepcopy(os.environ)
    os.environ.update(variables)
    yield
    os.environ = saved_env
