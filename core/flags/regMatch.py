import re
from core.flags import FlagType


class regMatch(FlagType):
    @staticmethod
    def execute(regex, value):
        """Matches the input using a regular expression matcher. See data/functions.json for argument information

        Returns:
            The result of the comparison
        """
        # Accounts for python wildcard bug
        if regex == "*":
            regex = "(.*)"
        pattern = re.compile(regex)
        match_obj = pattern.search(str(value))
        if match_obj:
            return True
        return False
