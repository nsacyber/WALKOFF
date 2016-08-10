

class ResultInfo(object):
    """Wrap the result of GetResultInfo"""

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

    def __str__(self):
        class_name = self.__class__.__name__
        q_id = getattr(self, 'question_id', -1)
        total_rows = getattr(self, 'row_count', -1)
        est_total = getattr(self, 'estimated_total', -1)
        passed = getattr(self, 'passed', -1)
        mr_passed = getattr(self, 'mr_passed', -1)
        tested = getattr(self, 'tested', -1)
        mr_tested = getattr(self, 'mr_tested', -1)
        ret_str = (
            '{} for ID {!r}, Total Rows: {}, EstTotal: {}, '
            'Passed: {}, MrPassed: {}, Tested: {}, MrTested: {}'
        ).format

        ret = ret_str(class_name, q_id, total_rows, est_total, passed,
                      mr_passed, tested, mr_tested)
        return ret

    @classmethod
    def fromSOAPElement(cls, el):
        """Deserialize a ResultInfo from a result_info SOAPElement

        Assumes all properties are integer values (true today)

        """
        result = ResultInfo()
        for property in vars(result):
            val = el.find('.//{}'.format(property))
            if val is not None and val.text:
                setattr(result, property, int(val.text))
        return result
