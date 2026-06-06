class ClassProperty:
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, obj, cls=None):
        if not cls: cls = type(obj)
        return self.getter.__get__(obj, cls)(cls)