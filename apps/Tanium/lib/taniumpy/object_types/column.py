from .sensor_types import SENSOR_TYPE_MAP


class Column(object):

    def __init__(self):
        self.what_hash = None
        self.display_name = None
        self.result_type = None

    def __str__(self):
        class_name = self.__class__.__name__
        val = self.display_name
        ret = '{}: {}'.format(class_name, val)
        return ret

    @classmethod
    def fromSOAPElement(cls, el):
        result = Column()
        val = el.find('wh')
        if val is not None:
            result.what_hash = int(val.text)
        val = el.find('dn')
        if val is not None:
            result.display_name = val.text
        val = el.find('rt')
        if val is not None:
            val = int(val.text)
            if val in SENSOR_TYPE_MAP:
                result.result_type = SENSOR_TYPE_MAP[val]
            else:
                result.result_type = int(val)

        return result
