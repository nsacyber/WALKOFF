class ClassA(object):
    staticfield1 = 'a'
    staticfield2 = 2

    def __init__(self):
        self.field1 = 1
        self.field2 = 'b'

    def public_func1(self, outer_param1):
        local_var = 1
        def inner_function(a):
            inner_variable = 'a'

    def public_func2(self):
        pass

    @staticmethod
    def public_static():
        pass

    @classmethod
    def public_class_method(cls):
        pass

    def _protected_func1(self):
        pass

    def __private_func1(self):
        pass

    def __iter__(self):
        while True:
            yield True


class ClassB(ClassA):
    pass



