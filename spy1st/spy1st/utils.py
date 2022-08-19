import threading

_local = threading.local()


def threading_local_var_get(name):
    return getattr(_local, name) if hasattr(_local, name) else None


def threading_local_var_set(name, value):
    setattr(_local, name, value)
