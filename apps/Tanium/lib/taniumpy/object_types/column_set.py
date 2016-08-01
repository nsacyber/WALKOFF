from .column import Column


class ColumnSet(object):

    def __init__(self):
        self.columns = []

    def __str__(self):
        class_name = self.__class__.__name__
        val = ', '.join([str(x.display_name) for x in self.columns])
        ret = '{}: {}'.format(class_name, val)
        return ret

    @classmethod
    def fromSOAPElement(cls, el):
        result = ColumnSet()
        columns = el.findall('./c')
        for column in columns:
            result.columns.append(Column.fromSOAPElement(column))
        return result

    def __len__(self):
        return len(self.columns)

    def __getitem__(self, ndx):
        return self.columns[ndx]
