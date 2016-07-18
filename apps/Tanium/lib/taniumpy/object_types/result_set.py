from .column_set import ColumnSet
from .row import Row
from .sensor import Sensor
import csv
import json
import re
from collections import OrderedDict


class ResultSet(object):
    """Wrap the result of GetResultData"""

    def __init__(self):
        self.age = None
        self.id = None
        self.report_count = None
        self.question_id = None
        self.archived_question_id = None
        self.seconds_since_issued = None
        self.issue_seconds = None
        self.expire_seconds = None
        self.tested = None
        self.passed = None
        self.mr_tested = None
        self.mr_passed = None
        self.estimated_total = None
        self.select_count = None
        self.row_count = None
        self.error_count = None
        self.no_result_count = None
        self.row_count_machines = None
        self.row_count_flag = None
        self.columns = None
        self.rows = None
        self.cache_id = None
        self.expiration = None
        self.filtered_row_count = None
        self.filtered_row_count_machines = None
        self.item_count = None

    def __str__(self):
        class_name = self.__class__.__name__
        q_id = getattr(self, 'question_id', -1)
        r_cols = len(getattr(self, 'columns', []) or [])
        total_rows = getattr(self, 'row_count', -1)
        current_rows = len(getattr(self, 'rows', []))
        est_total = getattr(self, 'estimated_total', -1)
        passed = getattr(self, 'passed', -1)
        mr_passed = getattr(self, 'mr_passed', -1)
        tested = getattr(self, 'tested', -1)
        mr_tested = getattr(self, 'mr_tested', -1)
        ret_str = (
            '{} for ID {!r}, Columns: {}, Total Rows: {}, Current Rows: {}, EstTotal: {}, '
            'Passed: {}, MrPassed: {}, Tested: {}, MrTested: {}'
        ).format

        ret = ret_str(class_name, q_id, r_cols, total_rows, current_rows, est_total, passed,
                      mr_passed, tested, mr_tested)
        return ret

    @classmethod
    def fromSOAPElement(cls, el):  # noqa
        """Deserialize a ResultSet from a result_set SOAPElement"""
        result = ResultSet()
        for property in vars(result):
            if property in ['column_set', 'row_set']:
                continue
            val = el.find('.//{}'.format(property))
            if val is not None and val.text:
                setattr(result, property, int(val.text))
        val = el.find('.//cs')
        if val is not None:
            result.columns = ColumnSet.fromSOAPElement(val)
        result.rows = []
        # TODO: Make sure that each "r" is a row, with one value
        # per column in "c/v". This was tested with just one client.
        rows = el.findall('.//rs/r')
        for row in rows:
            result.rows.append(Row.fromSOAPElement(row, result.columns))
        return result

    def to_jsonable(self, **kwargs):
        result = []
        for idx, r in enumerate(self.rows):
            new_row = []
            for h in self.columns:
                row_col = {
                    'column.display_name': h.display_name,
                    'column.what_hash': h.what_hash,
                    'column.result_type': h.result_type,
                    'column.values': r[h.display_name],
                }
                new_row.append(row_col)
            new_row = {'row{}'.format(idx): new_row}
            result.append(new_row)
        return result

    @staticmethod
    def to_json(jsonable, **kwargs):
        """Convert to a json string.

        jsonable must be a ResultSet instance

        """
        if not isinstance(jsonable, ResultSet):
            raise Exception("{} is not a ResultSet instance!".format(jsonable))

        return json.dumps(
            jsonable.to_jsonable(**kwargs),
            sort_keys=True,
            indent=2,
        )

    @staticmethod
    def write_csv(fd, val, **kwargs):
        def get_sort_headers(val, **kwargs):
            '''returns a list of sorted headers (Column names)

            '''
            header_sort = kwargs.get('header_sort', [])
            header_add_sensor = kwargs.get('header_add_sensor', False)
            header_add_type = kwargs.get('header_add_type', False)
            sensors = kwargs.get('sensors', [])

            headers = []
            for h in val.columns:
                h_name = h.display_name
                h_hash = h.what_hash
                h_type = h.result_type
                h_post = ''
                h_pre = ''

                '''
                if header is 'Count', check all row vals and if all are == 1,
                skip adding 'Count' header
                '''
                if h_name == 'Count':
                    count_vals = [int(r['Count'][0]) for r in val.rows]
                    count_gt_one = any([c > 1 for c in count_vals])
                    if not count_gt_one:
                        continue

                '''
                If kwargs has 'header_add_sensor=True':
                  look for 'sensors' in kwargs, if not there, throw exception
                  try to get matching sensor based off of what_hash
                  if no matching what_hash or sensor is not Sensor object,
                    throw exception
                  set h_pre to sensor name
                '''
                if header_add_sensor is True:
                    if not sensors or type(sensors) not in [tuple, list]:
                        err = (
                            "Must supply list of sensors used to produce this ResultSet in order "
                            "to add sensor name to columns!"
                        )
                        raise Exception(err)

                    match = None
                    for s in sensors:
                        if not isinstance(s, Sensor):
                            err = "{} is not a Sensor object".format(s)
                            raise Exception(err)

                        if s.hash == h_hash:
                            match = s.name
                            break

                    if h_name != 'Count':
                        if not match:
                            err = (
                                "Unable to find sensor matching what_hash {} in 'sensors' list!"
                            ).format(h_hash)
                            raise Exception(err)

                        h_pre = '{}: '.format(match)

                '''
                If kwargs has 'header_add_type=True':
                  set h_post to h_type
                '''
                if header_add_type is True:
                    h_post = ' ({})'.format(h_type)

                '''
                add a dictionary to sorted headers:
                    {
                     name: (without mods),
                     mod_name: (with mods),
                     hash: columns related sensor hash,
                    }
                '''
                headers.append({
                    'name': h_name,
                    'mod_name': '{}{}{}'.format(h_pre, h_name, h_post),
                    'hash': h_hash,
                })

            '''
            If kwargs has 'header_sort':
              if header_sort == False, do no sorting
              if header_sort == [] or True, do sorted(headers)
              if header_sort == ['col1', 'col2'], do sorted(headers), then
                put those headers first in order if they exist
            '''
            if header_sort is False:
                return headers
            elif header_sort is True:
                pass
            elif not type(header_sort) in [list, tuple]:
                raise Exception("header_sort must be a list!")

            # sort off of mod_name so that if sensor name is added to column
            # column name, sensor related columns will be grouped together
            sorted_headers = sorted(
                headers, key=lambda k: k['mod_name']
            )

            if header_sort is True or not header_sort:
                return sorted_headers

            custom_sorted_headers = []
            for hs in header_sort:
                for hidx, h in enumerate(sorted_headers):
                    if h['name'].lower() == hs.lower():
                        custom_sorted_headers.append(sorted_headers.pop(hidx))

            # append the rest of the sorted_headers that didn't
            # match header_sort
            custom_sorted_headers += sorted_headers
            return custom_sorted_headers

        def get_rows(val, headers, **kwargs):
            expand_grouped_columns = kwargs.get('expand_grouped_columns', False)

            rows = [[[str(v) for v in row[h['name']]] for h in headers] for row in val.rows]

            if expand_grouped_columns:
                rows = expand_rows(rows, headers)

            rows = [[fix_newlines('\n'.join(vals)) for vals in row] for row in rows]
            return rows

        def expand_rows(rows, headers):
            new_rows = []
            for row in rows:
                # if this row has no multi value rows (more than one value)
                # to expand, then just add it back into new rows and move on
                # to next one
                multi_vals = [len(v) > 1 for v in row]
                if not any(multi_vals):
                    new_rows.append(row)
                    continue
                new_rows += build_new_rows(row, headers)
            return new_rows

        def build_new_rows(row, headers):
            '''
            for each row in rows
            for each value_list in each row
            if the value_list len is 1, skip
            if the value_list len is more than 1,
              get all correlated columns,
              for each value in value_list,
              build a new row with index correlation from other
              multi val correlated columns, empty for non correlated
              multi val columns, and value copy for non correlated single
              columns
            '''
            new_rows = []
            done_hash = []

            for vals_idx, vals in enumerate(row):

                # don't expand single value row entries, they will be
                # added to each expanded row
                if not len(vals) > 1:
                    continue

                # get this values header
                val_h = headers[vals_idx]

                if val_h['hash'] in done_hash:
                    continue

                done_hash.append(val_h['hash'])

                # get all the related headers to this values header
                # (headers with same sensor hash)
                h_friends = [h for h in headers if h['hash'] == val_h['hash']]

                # build out a new row for each related multi value
                for val_idx, val in enumerate(vals):
                    new_rows.append(build_new_row(row, val_idx, h_friends, headers, val_h))
            return new_rows

        def build_new_row(row, val_idx, h_friends, headers, val_h):
            new_row = OrderedDict()
            for h_idx, h in enumerate(headers):
                h_hash = h['hash']
                h_name = h['name']
                if h_hash not in [f['hash'] for f in h_friends]:
                    if len(row[h_idx]) == 1:
                        # if this column is not correlated to the column we
                        # are working on and it's a single value, set
                        # it to the same value in the new row
                        new_row[h_name] = row[h_idx]
                    else:
                        # if this column is not correlated to the column we are
                        # working on and it is a multi value, set it
                        # to "UNRELATED"
                        new_row[h_name] = ["UNRELATED TO {}".format(val_h['mod_name'])]
                else:
                    # if this column is correlated to the column we are
                    # working on, set the value to the indexed value of this
                    # value
                    new_row[h_name] = [row[h_idx][val_idx]]
            new_row = new_row.values()
            return new_row

        def fix_newlines(val):
            if type(val) == str:
                # turn \n into \r\n
                val = re.sub(r"([^\r])\n", r"\1\r\n", val)
            return val

        if not isinstance(val, ResultSet):
            raise Exception("{} is not a ResultSet instance!".format(val))

        if val.columns is None:
            raise Exception("{} has no columns!".format(val))

        headers = get_sort_headers(val, **kwargs)
        rows = get_rows(val, headers, **kwargs)

        writer = csv.writer(fd)
        writer.writerow([h['mod_name'] for h in headers])
        writer.writerows(rows)
