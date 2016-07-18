

class Row(object):
    """A row in a result set.

    Values are stored in column order, also accessible
    by key using []
    """

    def __init__(self, columns):
        self.id = None
        self.cid = None
        self.vals = []
        self.columns = columns

    def __str__(self):
        class_name = self.__class__.__name__
        val = ', '.join([
            "{}:{}".format(
                self.columns[i].display_name,
                len(self.vals[i]),
            )
            for i, _ in enumerate(self.columns)
        ])
        ret = '{}: {}'.format(class_name, val)
        return ret

    @classmethod
    def fromSOAPElement(cls, el, columns):
        row = Row(columns)
        val = el.find("id")
        if val is not None:
            row.id = val.text
        val = el.find("cid")
        if val is not None:
            row.cid = val.text
        row_cols = el.findall("c")
        for rc in row_cols:
            row_vals = rc.findall("v")
            vals_text = [v.text for v in row_vals]
            row.vals.append(vals_text)
        return row

    def __len__(self):
        return len(self.vals)

    def __getitem__(self, column_name):
        for i in range(len(self.columns)):
            if self.columns[i].display_name == column_name:
                return self.vals[i]
        raise Exception('Column {} not found'.format(column_name))
