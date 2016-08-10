#!/usr/bin/env python
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
"""Collection of classes and methods for polling of actions/questions in :mod:`pytan`"""

import sys

# disable python from creating .pyc files everywhere
sys.dont_write_bytecode = True

import os
import logging
import time
import pprint
from datetime import datetime
from datetime import timedelta

my_file = os.path.abspath(__file__)
my_dir = os.path.dirname(my_file)
parent_dir = os.path.dirname(my_dir)
path_adds = [parent_dir]
[sys.path.insert(0, aa) for aa in path_adds if aa not in sys.path]

import taniumpy
import pytan


class QuestionPoller(object):
    """A class to poll the progress of a Question.

    The primary function of this class is to poll for result info for a question, and fire off events:

        * ProgressChanged
        * AnswersChanged
        * AnswersComplete

    Parameters
    ----------
    handler : :class:`pytan.handler.Handler`
        * PyTan handler to use for GetResultInfo calls
    obj : :class:`taniumpy.object_types.question.Question`
        * object to poll for progress
    polling_secs : int, optional
        * default: 5
        * Number of seconds to wait in between GetResultInfo loops
    complete_pct : int/float, optional
        * default: 99
        * Percentage of mr_tested out of estimated_total to consider the question "done"
    override_timeout_secs : int, optional
        * default: 0
        * If supplied and not 0, timeout in seconds instead of when object expires
    override_estimated_total : int, optional
        * instead of getting number of systems that should see this question from result_info.estimated_total, use this number
    force_passed_done_count : int, optional
        * when this number of systems have passed the right hand side of the question, consider the question complete
    """

    OBJECT_TYPE = taniumpy.object_types.question.Question
    """valid type of object that can be passed in as obj to __init__"""

    STR_ATTRS = [
        'object_info',
        'polling_secs',
        'override_timeout_secs',
        'complete_pct',
        'expiration',
    ]
    """Class attributes to include in __str__ output"""

    COMPLETE_PCT_DEFAULT = 99
    """default value for self.complete_pct"""

    POLLING_SECS_DEFAULT = 5
    """default value for self.polling_secs"""

    OVERRIDE_TIMEOUT_SECS_DEFAULT = 0
    """default value for self.override_timeout_secs"""

    EXPIRATION_ATTR = 'expiration'
    """attribute of self.obj that contains the expiration for this object"""

    EXPIRY_FALLBACK_SECS = 600
    """If the EXPIRATION_ATTR of `obj` can't be automatically determined, then this is used as a fallback for timeout - polling will failed after this many seconds if completion not reached"""

    obj = None
    """The object for this poller"""

    handler = None
    """The Handler object for this poller"""

    result_info = None
    """This will be updated with the ResultInfo object during run() calls"""

    _stop = False
    """Controls whether a run() loop should stop or not"""

    def __init__(self, handler, obj, **kwargs):
        self.methodlog = logging.getLogger("method_debug")
        self.DEBUG_METHOD_LOCALS = kwargs.get('debug_method_locals', False)

        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.setup_logging()

        if not isinstance(handler, pytan.handler.Handler):
            m = "{} is not a valid handler instance! Must be a: {!r}".format
            raise pytan.exceptions.PollingError(m(type(handler), pytan.handler.Handler))

        if not isinstance(obj, self.OBJECT_TYPE):
            m = "{} is not a valid object type! Must be a: {}".format
            raise pytan.exceptions.PollingError(m(type(obj), self.OBJECT_TYPE))

        self.handler = handler
        self.obj = obj
        self.polling_secs = kwargs.get('polling_secs', self.POLLING_SECS_DEFAULT)
        self.complete_pct = kwargs.get('complete_pct', self.COMPLETE_PCT_DEFAULT)
        self.override_timeout_secs = kwargs.get(
            'override_timeout_secs', self.OVERRIDE_TIMEOUT_SECS_DEFAULT,
        )
        self.force_passed_done_count = kwargs.get('force_passed_done_count', 0)

        self.id_str = "ID {}: ".format(getattr(self.obj, 'id', '-1'))
        self.obj_id = self._derive_attribute(attr='id', fallback=None)
        self.id_str = "ID {}: ".format(self.obj_id)
        self.poller_result = None
        self._post_init(**kwargs)

    def setup_logging(self):
        """Setup loggers for this object"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.qualname = "pytan.pollers.{}".format(self.__class__.__name__)
        self.mylog = logging.getLogger(self.qualname)
        self.progresslog = logging.getLogger(self.qualname + ".progress")
        self.resolverlog = logging.getLogger(self.qualname + ".resolver")

    def __str__(self):
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        class_name = self.__class__.__name__
        attrs = ", ".join(['{0}: "{1}"'.format(x, getattr(self, x, None)) for x in self.STR_ATTRS])
        ret = "{} {}".format(class_name, attrs)
        return ret

    def _post_init(self, **kwargs):
        """Post init class setup"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.override_estimated_total = kwargs.get('override_estimated_total', 0)
        self._derive_expiration(**kwargs)
        self._derive_object_info(**kwargs)

    def _refetch_obj(self, **kwargs):
        """Utility method to re-fetch a object

        This is used in the case that the obj supplied does not have all the metadata
        available
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        obj = self.handler._find(obj=self.obj, **clean_kwargs)

        if pytan.utils.empty_obj(obj):
            m = "Unable to find object: {}".format
            raise pytan.exceptions.PollingError(m(self.obj))

        self.obj = obj

    def _derive_attribute(self, attr, fallback='', **kwargs):
        """Derive an attributes value from self.obj

        Will re-fetch self.obj if the attribute is not set

        Parameters
        ----------
        attr : string
            string of attribute name to fetch from self.obj
        fallback : string
            value to fallback to if it still can't be accessed after re-fetching the obj
            if fallback is None, an exception will be raised

        Returns
        -------
        val : perspective
            The value of the attr from self.obj

        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj', 'pytan_help']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        val = getattr(self.obj, attr, None)

        # if attr isn't available on the object, maybe it's only a partial object
        # let's use the handler to re-fetch it
        if val is None:
            m = "{}attribute {!r} is not set, issuing GetObject to get the full object".format
            m = m(self.id_str, attr)
            self.resolverlog.debug(m)
            self._refetch_obj(pytan_help=m, **clean_kwargs)

        val = getattr(self.obj, attr, '')
        if val is None:
            if fallback is None:
                m = "{}{!r} is None, even after re-fetching object".format
                raise pytan.exceptions.PollingError(m(self.id_str, attr))

            m = (
                "{}attribute {!r} is not set after re-fetching object - using fallback of {}"
            ).format

            self.resolverlog.debug(m(self.id_str, attr, fallback))
            val = fallback

        m = "{}attribute '{}' resolved to '{}'".format
        self.mylog.debug(m(self.id_str, attr, val))
        return val

    def _derive_object_info(self, **kwargs):
        """Derive self.object_info from self.obj"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['attr', 'fallback']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        attr_name = 'query_text'
        fb = 'Unable to fetch question text'
        question_text = self._derive_attribute(attr=attr_name, fallback=fb, **clean_kwargs)

        attr_name = 'id'
        fb = -1
        question_id = self._derive_attribute(attr=attr_name, fallback=fb, **clean_kwargs)

        object_info = "Question ID: {}, Query: {}".format(question_id, question_text)

        m = "{}'object_info' resolved to '{}'".format
        self.resolverlog.debug(m(self.id_str, object_info))
        self.object_info = object_info

    def _derive_expiration(self, **kwargs):
        """Derive the expiration datetime string from a object

        Will generate a datetime string from self.EXPIRY_FALLBACK_SECS if unable to get the expiration from the object (self.obj) itself.
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['attr', 'fallback']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        attr_name = self.EXPIRATION_ATTR
        fb = pytan.utils.seconds_from_now(secs=self.EXPIRY_FALLBACK_SECS)
        self.expiration = self._derive_attribute(attr=attr_name, fallback=fb, **clean_kwargs)

    def run_callback(self, callbacks, callback, pct, **kwargs):
        """Utility method to find a callback in callbacks dict and run it
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if not callbacks.get(callback, ''):
            return

        cb_clean_keys = ['poller', 'pct']
        cb_clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=cb_clean_keys)

        try:
            m = "Running callback: {}".format
            self.mylog.debug(m(callback))
            callbacks[callback](poller=self, pct=pct, **cb_clean_kwargs)
        except Exception as e:
            m = "Exception occurred in '{}' Callback: {}".format
            self.mylog.warning(m(callback, e))

    def set_complect_pct(self, val): # noqa
        """Set the complete_pct to a new value

        Parameters
        ----------
        val : int/float
            float value representing the new percentage to consider self.obj complete
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.complete_pct = val

    def get_result_info(self, **kwargs):
        """Simple utility wrapper around :func:`pytan.handler.Handler.get_result_info`

        Parameters
        ----------
        gri_retry_count : int, optional
            * default: 10
            * Number of times to re-try GetResultInfo when estimated_total comes back as 0

        Returns
        -------
        result_info : :class:`taniumpy.object_types.result_info.ResultInfo`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        # add a retry to re-fetch result info if estimated_total == 0
        gri_retry_count = kwargs.get('gri_retry_count', 10)

        clean_keys = ['obj', 'gri_retry_count']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        current_try = 1

        while True:
            result_info = self.handler.get_result_info(obj=self.obj, **clean_kwargs)

            if result_info.estimated_total != 0:
                break

            attempt_text = "attempt {} out of {}".format(current_try, gri_retry_count)
            if current_try >= gri_retry_count:
                m = "Estimated Total of Clients is 0 -- no clients available?, {}".format
                raise pytan.exceptions.PollingError(m(attempt_text))
            else:
                current_try += 1
                h = "Re-issuing a GetResultInfo since the estimated_total came back 0, {}".format
                clean_kwargs['pytan_help'] = h(attempt_text)
                self.mylog.debug(h(attempt_text))
                time.sleep(1)
                continue

        return result_info

    def get_result_data(self, **kwargs):
        """Simple utility wrapper around :func:`pytan.handler.Handler.get_result_data`

        Returns
        -------
        result_data : :class:`taniumpy.object_types.result_set.ResultSet`
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)
        result_data = self.handler.get_result_data(obj=self.obj, **clean_kwargs)
        return result_data

    def run(self, callbacks={}, **kwargs):
        """Poll for question data and issue callbacks.

        Parameters
        ----------
        callbacks : dict
            * Callbacks should be a dict with any of these members:
                * 'ProgressChanged'
                * 'AnswersChanged'
                * 'AnswersComplete'

            * Each callback should be a function that accepts:
                * 'poller': a poller instance
                * 'pct': a percent complete
                * 'kwargs': a dict of other args
        gri_retry_count : int, optional
            * default: 10
            * Number of times to re-try GetResultInfo when estimated_total comes back as 0

        Notes
        -----
            * Any callback can choose to get data from the session by calling poller.get_result_data() or new info by calling poller.get_result_info()
            * Any callback can choose to stop the poller by calling poller.stop()
            * Polling will be stopped only when one of the callbacks calls the stop() method or the answers are complete.
            * Any callback can call setPercentCompleteThreshold to change what "done" means on the fly
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.start = datetime.utcnow()
        self.expiration_timeout = pytan.utils.timestr_to_datetime(timestr=self.expiration)

        if self.override_timeout_secs:
            td_obj = timedelta(seconds=self.override_timeout_secs)
            self.override_timeout = self.start + td_obj
        else:
            self.override_timeout = None

        clean_keys = ['callbacks']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        self.passed_eq_total = self.passed_eq_est_total_loop(callbacks=callbacks, **clean_kwargs)
        self.poller_result = all([self.passed_eq_total])
        return self.poller_result

    def passed_eq_est_total_loop(self, callbacks={}, **kwargs):
        """Method to poll Result Info for self.obj until the percentage of 'passed' out of 'estimated_total' is greater than or equal to self.complete_pct
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        # current percentage tracker
        self.pct = None
        # loop counter
        self.loop_count = 1
        # establish a previous result_info that's empty
        self.previous_result_info = taniumpy.object_types.result_info.ResultInfo()

        while not self._stop:
            # perform a GetResultInfo SOAP call
            clean_keys = ['pytan_help', 'callback', 'pct']
            clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

            h = "Issue a GetResultInfo for a Question to check the current progress of answers"
            self.result_info = self.get_result_info(pytan_help=h, **clean_kwargs)

            # derive the current percentage of completion by calculating percentage of
            # mr_tested out of estimated_total
            # mr_tested = number of systems that have seen the question
            # estimated_total = rough estimate of total number of systems
            # passed = number of systems that have passed any filters for the question
            tested = self.result_info.mr_tested
            est_total = self.override_estimated_total or self.result_info.estimated_total
            passed = self.result_info.passed

            new_pct = pytan.utils.get_percentage(part=tested, whole=est_total)
            new_pct_str = "{0:.0f}%".format(new_pct)
            complete_pct_str = "{0:.0f}%".format(self.complete_pct)

            # print a progress debug string
            self.progress_str = (
                "Progress: Tested: {0.tested}, Passed: {0.passed}, "
                "MR Tested: {0.mr_tested}, MR Passed: {0.mr_passed}, "
                "Est Total: {0.estimated_total}, Row Count: {0.row_count}, Override Est Total: {1}"
            ).format(self.result_info, self.override_estimated_total)
            self.progresslog.debug("{}{}".format(self.id_str, self.progress_str))

            # print a timing debug string
            if self.override_timeout:
                time_till_expiry = self.override_timeout - datetime.utcnow()
            else:
                time_till_expiry = self.expiration_timeout - datetime.utcnow()

            self.timing_str = (
                "Timing: Started: {}, Expiration: {}, Override Timeout: {}, "
                "Elapsed Time: {}, Left till expiry: {}, Loop Count: {}"
            ).format(
                self.start,
                self.expiration_timeout,
                self.override_timeout,
                datetime.utcnow() - self.start,
                time_till_expiry,
                self.loop_count,
            )
            self.progresslog.debug("{}{}".format(self.id_str, self.timing_str))

            # check to see if progress has changed, if so run the callback
            progress_changed = any([
                self.previous_result_info.tested != self.result_info.tested,
                self.previous_result_info.passed != self.result_info.passed,
                self.previous_result_info.mr_tested != self.result_info.mr_tested,
                self.previous_result_info.mr_passed != self.result_info.mr_passed,
                self.previous_result_info.estimated_total != self.result_info.estimated_total,
                self.pct != new_pct,
            ])

            if progress_changed:
                m = "{}Progress Changed {} ({} of {})".format
                self.progresslog.info(m(self.id_str, new_pct_str, tested, est_total))
                cb = 'ProgressChanged'
                self.run_callback(callbacks=callbacks, callback=cb, pct=new_pct, **clean_kwargs)

            # check to see if answers have changed, if so run the callback
            answers_changed = any([
                self.previous_result_info.tested != self.result_info.tested,
                self.previous_result_info.passed != self.result_info.passed,
            ])

            if answers_changed:
                cb = 'AnswersChanged'
                self.run_callback(callbacks=callbacks, callback=cb, pct=new_pct, **clean_kwargs)

            # check to see if new_pct has reached complete_pct threshold, if so return True
            if new_pct >= self.complete_pct:
                m = "{}Reached Threshold of {} ({} of {})".format
                self.mylog.info(m(self.id_str, complete_pct_str, tested, est_total))
                cb = 'AnswersComplete'
                self.run_callback(callbacks=callbacks, callback=cb, pct=new_pct, **clean_kwargs)
                return True

            if self.force_passed_done_count and passed >= self.force_passed_done_count:
                m = "{}Reached forced passed done count of {} ({} of {})".format
                self.mylog.info(m(self.id_str, self.force_passed_done_count, tested, est_total))
                cb = 'AnswersComplete'
                self.run_callback(callbacks=callbacks, callback=cb, pct=new_pct, **clean_kwargs)
                return True

            # check to see if override timeout is specified, if so and we have passed it, return
            # False
            if self.override_timeout and datetime.utcnow() >= self.override_timeout:
                m = "{}Reached override timeout of {}".format
                self.mylog.warning(m(self.id_str, self.override_timeout))
                return False

            # check to see if we have passed the actions expiration timeout, if so return False
            if datetime.utcnow() >= self.expiration_timeout:
                m = "{}Reached expiration timeout of {}".format
                self.mylog.warning(m(self.id_str, self.expiration_timeout))
                return False

            # if stop is called, return True
            if self._stop:
                m = "{}Stop called at {}".format
                self.mylog.info(m(self.id_str, new_pct_str))
                return False

            # update our class variables to the new values determined by this loop
            self.pct = new_pct
            self.previous_result_info = self.result_info

            time.sleep(self.polling_secs)
            self.loop_count += 1

    def stop(self):
        self._stop = True

    def _debug_locals(self, fname, flocals):
        """Method to print out locals for a function if self.DEBUG_METHOD_LOCALS is True"""
        if getattr(self, 'DEBUG_METHOD_LOCALS', False):
            m = "Local variables for {}.{}:\n{}".format
            self.methodlog.debug(m(self.__class__.__name__, fname, pprint.pformat(flocals)))


class ActionPoller(QuestionPoller):
    """A class to poll the progress of an Action.

    The primary function of this class is to poll for result info for an action, and fire off events:
        * 'SeenProgressChanged'
        * 'SeenAnswersComplete'
        * 'FinishedProgressChanged'
        * 'FinishedAnswersComplete'

    Parameters
    ----------
    handler : :class:`pytan.handler.Handler`
        * PyTan handler to use for GetResultInfo calls
    obj : :class:`taniumpy.object_types.action.Action`
        * object to poll for progress
    polling_secs : int, optional
        * default: 5
        * Number of seconds to wait in between GetResultInfo loops
    complete_pct : int/float, optional
        * default: 100
        * Percentage of passed_count out of successfully run actions to consider the action "done"
    override_timeout_secs : int, optional
        * default: 0
        * If supplied and not 0, timeout in seconds instead of when object expires
    override_passed_count : int, optional
        * instead of getting number of systems that should run this action by asking a question, use this number
    """

    OBJECT_TYPE = taniumpy.object_types.action.Action
    """valid type of object that can be passed in as obj to __init__"""

    COMPLETE_PCT_DEFAULT = 100
    """default value for self.complete_pct"""

    ACTION_DONE_KEY = 'success'
    """key in action_result_map that maps to an action being done"""

    RUNNING_STATUSES = ["active", "open"]
    """values for status attribute of action object that mean the action is running"""

    EXPIRATION_ATTR = 'expiration_time'
    """attribute of self.obj that contains the expiration for this object"""

    def _post_init(self, **kwargs):
        """Post init class setup"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.override_passed_count = kwargs.get('override_passed_count', 0)
        self._derive_package_spec(**kwargs)
        self._derive_target_group(**kwargs)
        self._derive_verify_enabled(**kwargs)
        self._derive_result_map(**kwargs)
        self._derive_expiration(**kwargs)
        self._derive_status(**kwargs)
        self._derive_stopped_flag(**kwargs)
        self._derive_object_info(**kwargs)

    def _derive_status(self, **kwargs):
        """Get the status attribute for self.obj"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['attr', 'fallback']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        attr_name = 'status'
        fb = None
        self.status = self._derive_attribute(attr=attr_name, fallback=fb, **clean_kwargs)

    def _derive_stopped_flag(self, **kwargs):
        """Get the stopped_flag attribute for self.obj"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['attr', 'fallback']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        attr_name = 'stopped_flag'
        fb = None
        self.stopped_flag = self._derive_attribute(attr=attr_name, fallback=fb, **clean_kwargs)
        self.stopped_flag = int(self.stopped_flag)
        self.stopped_flag = bool(self.stopped_flag)

    def _derive_package_spec(self, **kwargs):
        """Get the package_spec attribute for self.obj, then fetch the full package_spec object"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['attr', 'fallback', 'obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        attr_name = 'package_spec'
        fb = None
        self.package_spec = self._derive_attribute(attr=attr_name, fallback=fb, **clean_kwargs)

        # get the full package object associated with this action
        h = "Issue a GetObject on the package for an action to get the full object"
        clean_kwargs['pytan_help'] = h
        self.package_spec = self.handler._find(obj=self.package_spec, **clean_kwargs)

    def _derive_target_group(self, **kwargs):
        """Get the target_group attribute for self.obj, then fetch the full group object"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['attr', 'fallback', 'obj']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        attr_name = 'target_group'
        fb = None
        self.target_group = self._derive_attribute(attr=attr_name, fallback=fb, **clean_kwargs)

        # if the target group id is not 0, re-fetch the full group object
        if int(self.target_group.id) != 0:
            h = (
                "Issue a GetObject on the target_group for an action to get the full Group "
                "object"
            )
            clean_kwargs['pytan_help'] = h
            try:
                self.target_group = self.handler._find(obj=self.target_group, **clean_kwargs)
                self._fix_group(g=self.target_group)
                self.passed_count_reliable = True
            except:
                self.passed_count_reliable = False
                m = "{}Passed Count unreliable! Unable to find Actions Target Group: {}".format
                self.mylog.exception(m(self.id_str, self.target_group))

    def _fix_group(self, g, **kwargs):
        """Sets ID to null on a group object and all of it's sub_groups, needed for 6.5"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        g.id = None
        if g.sub_groups:
            for x in g.sub_groups:
                self._fix_group(g=x)

    def _derive_verify_enabled(self, **kwargs):
        """Determine if this action has verification enabled"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.verify_enabled = False
        package_spec = getattr(self, 'package_spec', None)
        ps_verify_group_id = getattr(package_spec, 'verify_group_id', None)
        vg = getattr(package_spec, 'verify_group', None)
        vg_id = getattr(vg, 'id', None)
        if ps_verify_group_id or vg_id:
            self.verify_enabled = True

    def _derive_result_map(self, **kwargs):
        """Determine what self.result_map should contain for the various statuses an action can have

        A package object has to have a verify_group defined on it in order
        for deploy action verification to trigger. That can be only done
        at package creation/update

        If verify_enable is True, then the various result states for an action change
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        if self.verify_enabled:
            finished = [
                'Verified.', 'Succeeded.', 'Expired.', 'Stopped.', 'NotSucceeded.', 'Failed.',
            ]
            success = [
                'Verified.',
            ]
            running = [
                'Completed.', 'PendingVerification.', 'Copying.', 'Waiting.', 'Downloading.',
                'Running.',
            ]
            failed = [
                'Expired.', 'Stopped.', 'NotSucceeded.', 'Failed.',
            ]
        else:
            finished = [
                'Verified.', 'Succeeded.', 'Completed.', 'Expired.', 'Stopped.', 'NotSucceeded.',
                'Failed.',
            ]
            success = [
                'Verified.', 'Completed.',
            ]
            running = [
                'PendingVerification.', 'Copying.', 'Waiting.', 'Downloading.', 'Running.',
            ]
            failed = [
                'Expired.', 'Stopped.', 'NotSucceeded.', 'Failed.',
            ]

        self.result_map = {
            'finished': {"{}:{}".format(self.obj.id, k): [] for k in finished},
            'success': {"{}:{}".format(self.obj.id, k): [] for k in success},
            'running': {"{}:{}".format(self.obj.id, k): [] for k in running},
            'failed': {"{}:{}".format(self.obj.id, k): [] for k in failed},
            'unknown': {},
        }
        for k, v in self.result_map.iteritems():
            v['total'] = 0

        m = "{}Result Map resolved to {}".format
        self.resolverlog.debug(m(self.id_str, self.result_map))

    def _derive_object_info(self, **kwargs):
        """Derive self.object_info from self.obj"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        m = "{}Package: '{}', Target: '{}', Verify: {}, Stopped: {}, Status: {}".format

        object_info = m(
            self.id_str, self.package_spec.name, self.target_group.text, self.verify_enabled,
            self.stopped_flag, self.status,
        )

        m = "{}Object Info resolved to {}".format
        self.resolverlog.debug(m(self.id_str, object_info))

        self.object_info = object_info

    def run(self, callbacks={}, **kwargs):
        """Poll for action data and issue callbacks.

        Parameters
        ----------
        callbacks : dict
            * Callbacks should be a dict with any of these members:
                * 'SeenProgressChanged'
                * 'SeenAnswersComplete'
                * 'FinishedProgressChanged'
                * 'FinishedAnswersComplete'

            * Each callback should be a function that accepts:
                * 'poller': a poller instance
                * 'pct': a percent complete
                * 'kwargs': a dict of other args

        Notes
        -----
            * Any callback can choose to get data from the session by calling :func:`pytan.poller.QuestionPoller.get_result_data` or new info by calling :func:`pytan.poller.QuestionPoller.get_result_info`
            * Any callback can choose to stop the poller by calling :func:`pytan.poller.QuestionPoller.stop`
            * Polling will be stopped only when one of the callbacks calls the :func:`pytan.poller.QuestionPoller.stop` method or the answers are complete.
            * Any callbacks can call :func:`pytan.poller.QuestionPoller.setPercentCompleteThreshold` to change what "done" means on the fly
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.start = datetime.utcnow()
        self.expiration_timeout = pytan.utils.timestr_to_datetime(timestr=self.expiration)

        if self.override_timeout_secs:
            td_obj = timedelta(seconds=self.override_timeout_secs)
            self.override_timeout = self.start + td_obj
        else:
            self.override_timeout = None

        clean_keys = ['callbacks', 'obj', 'pytan_help', 'handler']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        if self.override_passed_count:
            self.passed_count = self.override_passed_count
            m = "{}passed_count resolved override of {}".format
            self.mylog.debug(m(self.id_str, self.override_passed_count))
        else:
            m = (
                "{}Issuing an AddObject of a Question object with no Selects and the same Group "
                "used by the Action object. The number of systems that should successfully run "
                "the Action will be taken from result_info.passed_count for the Question asked "
                "when all answers for the question have reported in."
            ).format
            self.mylog.debug(m(self.id_str, self.obj))

            self.pre_question = taniumpy.Question()
            self.pre_question.group = self.target_group
            self.pre_question = self.handler._add(
                obj=self.pre_question, pytan_help=m(self.id_str, self.obj), **clean_kwargs
            )

            self.pre_question_poller = pytan.pollers.QuestionPoller(
                handler=self.handler, obj=self.pre_question, **clean_kwargs
            )

            self.pre_question_poller.run(callbacks=callbacks, **clean_kwargs)

            self.passed_count = self.pre_question_poller.result_info.passed

            m = "{}passed_count resolved to {}".format
            self.mylog.debug(m(self.id_str, self.passed_count))

        self.seen_eq_passed = self.seen_eq_passed_loop(callbacks=callbacks, **clean_kwargs)
        self.finished_eq_passed = self.finished_eq_passed_loop(callbacks=callbacks, **clean_kwargs)
        self.poller_result = all([self.seen_eq_passed, self.finished_eq_passed])
        return self.poller_result

    def seen_eq_passed_loop(self, callbacks={}, **kwargs):
        """Method to poll Result Info for self.obj until the percentage of 'seen_count' out of 'self.passed_count' is greater than or equal to self.complete_pct

        * seen_count is calculated from an aggregate GetResultData
        * self.passed_count is calculated by the question asked before this method is called. that question has no selects, but has a group that is the same group as the action for this object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        # number of systems that have SEEN the action
        self.seen_count = None
        # current percentage tracker
        self.seen_pct = None
        # loop counter
        self.seen_loop_count = 1
        # establish a previous result_info that's empty
        self.previous_result_info = taniumpy.object_types.result_info.ResultInfo()
        # establish a previous result_data that's empty
        self.previous_result_data = taniumpy.object_types.result_set.ResultSet()

        if self.passed_count == 0:
            m = "Passed Count of Clients for filter {} is 0 -- no clients match filter".format
            self.mylog.warning(m(self.target_group.text))
            return False

        while not self._stop:
            clean_keys = ['pytan_help', 'aggregate', 'callback', 'pct']
            clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

            # re-fetch object and re-derive stopped flag and status
            h = (
                "Issue a GetObject for an Action in order to have access to the latest values for "
                "stopped_flag and status"
            )
            self._refetch_obj(pytan_help=h, **clean_kwargs)
            self._derive_stopped_flag(**clean_kwargs)
            self._derive_status(**clean_kwargs)

            # perform a GetResultInfo SOAP call, this ensures fresh data is available for
            # GetResultData
            h = (
                "Issue a GetResultInfo for an Action to ensure fresh data is available for a "
                "GetResultData call"
            )
            self.result_info = self.get_result_info(pytan_help=h, **clean_kwargs)

            # get the aggregate resultdata
            h = (
                "Issue a GetResultData with the aggregate option set to True."
                "This will return row counts of machines that have answered instead of"
                " all the data"
            )
            self.result_data = self.get_result_data(aggregate=True, pytan_help=h, **clean_kwargs)

            # add up the Count column for all rows
            # this count will equate to the number of systems that have started to process
            # this action in any way
            seen_count = sum([int(x['Count'][0]) for x in self.result_data.rows])

            # we use self.passed_count from the question we asked to get the number of matching
            # systems for determining the current pct of completion
            new_pct = pytan.utils.get_percentage(part=seen_count, whole=self.passed_count)
            new_pct_str = "{0:.0f}%".format(new_pct)
            complete_pct_str = "{0:.0f}%".format(self.complete_pct)

            # print a progress debug string
            self.progress_str = (
                "Progress: Seen Action: {}, Expected Seen: {}, Percent: {}"
            ).format(seen_count, self.passed_count, new_pct_str)
            self.progresslog.debug("{}{}".format(self.id_str, self.progress_str))

            # print a timing debug string
            if self.override_timeout:
                time_till_expiry = self.override_timeout - datetime.utcnow()
            else:
                time_till_expiry = self.expiration_timeout - datetime.utcnow()

            self.timing_str = (
                "Timing: Started: {}, Expiration: {}, Override Timeout: {}, "
                "Elapsed Time: {}, Left till expiry: {}, Loop Count: {}"
            ).format(
                self.start,
                self.expiration_timeout,
                self.override_timeout,
                datetime.utcnow() - self.start,
                time_till_expiry,
                self.seen_loop_count,
            )
            self.progresslog.debug("{}{}".format(self.id_str, self.timing_str))

            # check to see if progress has changed, if so run the callback
            seen_changed = seen_count != self.seen_count
            pct_changed = self.seen_pct != new_pct
            progress_changed = any([seen_changed, pct_changed])

            if progress_changed:
                m = "{}Progress Changed for Seen Count {} ({} of {})".format
                self.progresslog.info(m(self.id_str, new_pct_str, seen_count, self.passed_count))
                cb = 'SeenProgressChanged'
                self.run_callback(callbacks=callbacks, callback=cb, pct=new_pct, **clean_kwargs)

            # check to see if new_pct has reached complete_pct threshold, if so return True
            if new_pct >= self.complete_pct:
                m = "{}Reached Threshold for Seen Count of {} ({} of {})".format
                m = m(self.id_str, complete_pct_str, seen_count, self.passed_count)
                self.mylog.info(m)
                cb = 'SeenAnswersComplete'
                self.run_callback(callbacks=callbacks, callback=cb, pct=new_pct, **clean_kwargs)
                return True

            # check to see if override timeout is specified, if so and we have passed it, return
            # False
            if self.override_timeout and datetime.utcnow() >= self.override_timeout:
                m = "{}Reached override timeout of {}".format
                self.mylog.warning(m(self.id_str, self.override_timeout))
                return False

            # check to see if we have passed the actions expiration timeout, if so return False
            if datetime.utcnow() >= self.expiration_timeout:
                m = "{}Reached expiration timeout of {}".format
                self.mylog.warning(m(self.id_str, self.expiration))
                return False

            # check to see if action is stopped, if it is, return False
            if self.stopped_flag:
                m = "{}Actions stopped flag is True".format
                self.mylog.warning(m(self.id_str))
                return False

            # check to see if action is not active, if it is not, False
            if self.status.lower() not in self.RUNNING_STATUSES:
                m = "{}Action status is {}, which is not one of: {}".format
                m = m(self.id_str, self.status, ', '.join(self.RUNNING_STATUSES))
                self.mylog.warning(m)
                return False

            # if stop is called, return True
            if self._stop:
                m = "{}Stop called at {}".format
                self.mylog.info(m(self.id_str, new_pct_str))
                return True

            # update our class variables to the new values determined by this loop
            self.seen_pct = new_pct
            self.seen_count = seen_count
            self.previous_result_info = self.result_info
            self.previous_result_data = self.result_data

            time.sleep(self.polling_secs)
            self.seen_loop_count += 1

    def finished_eq_passed_loop(self, callbacks={}, **kwargs):
        """Method to poll Result Info for self.obj until the percentage of 'finished_count' out of 'self.passed_count' is greater than or equal to self.complete_pct

        * finished_count is calculated from a full GetResultData call that is parsed into self.action_result_map
        * self.passed_count is calculated by the question asked before this method is called. that question has no selects, but has a group that is the same group as the action for this object
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        # number of systems that have FINISHED the action
        self.finished_count = None
        # current percentage tracker
        self.finished_pct = None
        # loop counter
        self.loop_count = 1
        # establish a previous result_info that's empty
        self.previous_result_info = taniumpy.object_types.result_info.ResultInfo()
        # establish a previous result_data that's empty
        self.previous_result_data = taniumpy.object_types.result_set.ResultSet()

        while not self._stop:
            clean_keys = ['pytan_help', 'aggregate', 'callback', 'pct']
            clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

            # re-fetch object and re-derive stopped flag and status
            h = (
                "Issue a GetObject for an Action in order to have access to the latest values for "
                "stopped_flag and status"
            )
            self._refetch_obj(pytan_help=h, **clean_kwargs)
            self._derive_stopped_flag(**clean_kwargs)
            self._derive_status(**clean_kwargs)

            # perform a GetResultInfo SOAP call, this ensures fresh data is available for
            # GetResultData
            h = (
                "Issue a GetResultInfo for an Action to ensure fresh data is available for a "
                "GetResultData call"
            )
            self.result_info = self.get_result_info(pytan_help=h, **clean_kwargs)

            # get the NON aggregate resultdata
            h = (
                "Issue a GetResultData for an Action with the aggregate option set to False. "
                "This will return all of the Action Statuses for each computer that have run this "
                "Action"
            )
            self.result_data = self.get_result_data(aggregate=False, pytan_help=h, **clean_kwargs)

            """
            for each row from the result data
            get the computer name and the action status for this row
            add the computer name to the appropriate action status in self.result_map
            """
            for row in self.result_data.rows:
                action_status = row['Action Statuses'][0]
                comp_name = row['Computer Name'][0]
                known = False

                for s, smap in self.result_map.iteritems():
                    if action_status in smap:
                        known = True
                        if comp_name not in self.result_map[s][action_status]:
                            self.result_map[s][action_status].append(comp_name)

                if not known:
                    if action_status not in self.result_map['unknown']:
                        self.result_map['unknown'][action_status] = []

                    if comp_name not in self.result_map['unknown'][action_status]:
                        self.result_map['unknown'][action_status].append(comp_name)

                for s, smap in self.result_map.iteritems():
                    smap['total'] = sum([len(y) for x, y in smap.iteritems() if x != 'total'])

            # Use the total from the key defined in self.ACTION_DONE_KEY in self.result_map
            # this total will equate to the number of systems that have finished this action
            finished_count = self.result_map[self.ACTION_DONE_KEY]['total']

            # we use self.passed_count from the question we asked to get the number of matching
            # systems for determining the current pct of completion
            new_pct = pytan.utils.get_percentage(part=finished_count, whole=self.passed_count)
            new_pct_str = "{0:.0f}%".format(new_pct)
            complete_pct_str = "{0:.0f}%".format(self.complete_pct)

            # print a progress debug string
            p = "{}: {}".format
            progress_list = [p(s, smap['total']) for s, smap in self.result_map.iteritems()]
            progress_list.append("Done Key: {}".format(self.ACTION_DONE_KEY))
            progress_list.append("Passed Count: {}".format(self.passed_count))
            self.progress_str = ', '.join(progress_list)
            self.progresslog.debug("{}{}".format(self.id_str, self.progress_str))

            # print a timing debug string
            if self.override_timeout:
                time_till_expiry = self.override_timeout - datetime.utcnow()
            else:
                time_till_expiry = self.expiration_timeout - datetime.utcnow()

            self.timing_str = (
                "Timing: Started: {}, Expiration: {}, Override Timeout: {}, "
                "Elapsed Time: {}, Left till expiry: {}, Loop Count: {}"
            ).format(
                self.start,
                self.expiration_timeout,
                self.override_timeout,
                datetime.utcnow() - self.start,
                time_till_expiry,
                self.loop_count,
            )
            self.progresslog.debug("{}{}".format(self.id_str, self.timing_str))

            # check to see if progress has changed, if so run the callback
            finished_changed = finished_count != self.finished_count
            pct_changed = self.finished_pct != new_pct
            progress_changed = any([finished_changed, pct_changed])

            if progress_changed:
                m = "{}Progress Changed for Finished Count {} ({} of {})".format
                m = m(self.id_str, new_pct_str, finished_count, self.passed_count)
                self.progresslog.info(m)
                cb = 'FinishedProgressChanged'
                self.run_callback(callbacks=callbacks, callback=cb, pct=new_pct, **clean_kwargs)

            # check to see if new_pct has reached complete_pct threshold, if so return True
            if new_pct >= self.complete_pct:
                m = "{}Reached Threshold for Finished Count of {} ({} of {})".format
                m = m(self.id_str, complete_pct_str, finished_count, self.passed_count)
                self.mylog.info(m)
                cb = 'FinishedAnswersComplete'
                self.run_callback(callbacks=callbacks, callback=cb, pct=new_pct, **clean_kwargs)
                return True

            # check to see if override timeout is specified, if so and we have passed it, return
            # False
            if self.override_timeout and datetime.utcnow() >= self.override_timeout:
                m = "{}Reached override timeout of {}".format
                self.mylog.warning(m(self.id_str, self.override_timeout))
                return False

            # check to see if we have passed the actions expiration timeout, if so return False
            if datetime.utcnow() >= self.expiration_timeout:
                m = "{}Reached expiration timeout of {}".format
                self.mylog.warning(m(self.id_str, self.expiration))
                return False

            # check to see if action is stopped, if it is, return False
            if self.stopped_flag:
                m = "{}Actions stopped flag is True".format
                self.mylog.warning(m(self.id_str))
                return False

            # check to see if action is not active, if it is not, False
            if self.status.lower() not in self.RUNNING_STATUSES:
                m = "{}Action status is {}, which is not one of: {}".format
                m = m(self.id_str, self.status, ', '.join(self.RUNNING_STATUSES))
                self.mylog.warning(m)
                return False

            # if stop is called, return True
            if self._stop:
                m = "{}Stop called at {}".format
                self.mylog.info(m(self.id_str, new_pct_str))
                return True

            # update our class variables to the new values determined by this loop
            self.finished_pct = new_pct
            self.finished_count = finished_count
            self.previous_result_info = self.result_info
            self.previous_result_data = self.result_data

            time.sleep(self.polling_secs)
            self.loop_count += 1


class SSEPoller(QuestionPoller):
    """A class to poll the progress of a Server Side Export.

    The primary function of this class is to poll for status of server side exports.

    Parameters
    ----------
    handler : :class:`pytan.handler.Handler`
        PyTan handler to use for GetResultInfo calls
    export_id : str
        * ID of server side export
    polling_secs : int, optional
        * default: 2
        * Number of seconds to wait in between status check loops
    timeout_secs : int, optional
        * default: 600
        * timeout in seconds for waiting for status completion, 0 does not time out
    """
    STR_ATTRS = [
        'export_id',
        'polling_secs',
        'timeout_secs',
        'sse_status',
    ]
    """Class attributes to include in __str__ output"""

    POLLING_SECS_DEFAULT = 2
    """default value for self.polling_secs"""

    TIMEOUT_SECS_DEFAULT = 600
    """default value for self.timeout_secs"""

    export_id = None
    """The export_id for this poller"""

    def __init__(self, handler, export_id, **kwargs):
        self.methodlog = logging.getLogger("method_debug")
        self.DEBUG_METHOD_LOCALS = kwargs.get('debug_method_locals', False)

        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.setup_logging()

        if not isinstance(handler, pytan.handler.Handler):
            m = "{} is not a valid handler instance! Must be a: {!r}".format
            raise pytan.exceptions.PollingError(m(type(handler), pytan.handler.Handler))

        self.handler = handler
        self.export_id = export_id
        self.polling_secs = kwargs.get('polling_secs', self.POLLING_SECS_DEFAULT)
        self.timeout_secs = kwargs.get('timeout_secs', self.TIMEOUT_SECS_DEFAULT)

        self.id_str = "ID '{}': ".format(export_id)
        self.poller_result = None
        self.sse_status = "Not yet run"
        self._post_init(**kwargs)

    def _post_init(self, **kwargs):
        """Post init class setup"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        pass

    def get_sse_status(self, **kwargs):
        """Function to get the status of a server side export

        Constructs a URL via: export/${export_id}.status and performs an authenticated HTTP get
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['url']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        export_id = kwargs.get('export_id', self.export_id)
        short_url = 'export/{}.status'.format(export_id)
        full_url = self.handler.session._full_url(url=short_url)

        h = "Perform an HTTP get to retrieve the status of a server side export"
        clean_kwargs['pytan_help'] = clean_kwargs.get('pytan_help', h)

        ret = self.handler.session.http_get(url=short_url, **clean_kwargs).strip()

        # print a progress debug string
        progress_str = "Server Side Export Progress: '{}' from URL: {}".format
        progress_str = progress_str(ret, full_url)
        self.progresslog.debug("{}{}".format(self.id_str, progress_str))

        return ret

    def get_sse_data(self, **kwargs):
        """Function to get the data of a server side export

        Constructs a URL via: export/${export_id}.gz and performs an authenticated HTTP get
        """
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        clean_keys = ['url']
        clean_kwargs = pytan.utils.clean_kwargs(kwargs=kwargs, keys=clean_keys)

        export_id = kwargs.get('export_id', self.export_id)
        short_url = 'export/{}.gz'.format(export_id)
        full_url = self.handler.session._full_url(url=short_url)

        h = "Perform an HTTP get to retrieve the data of a server side export"
        clean_kwargs['pytan_help'] = clean_kwargs.get('pytan_help', h)

        ret = self.handler.session.http_get(url=short_url, **clean_kwargs)

        # print a progress debug string
        progress_str = "Server Side Export Data Length: {} from URL: {}".format
        progress_str = progress_str(len(ret), full_url)
        self.progresslog.debug("{}{}".format(self.id_str, progress_str))

        return ret

    def run(self, **kwargs):
        """Poll for server side export status"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        self.start = datetime.utcnow()

        if self.timeout_secs:
            td_obj = timedelta(seconds=self.timeout_secs)
            self.timeout = self.start + td_obj
        else:
            self.timeout = None

        self.sse_status_completed = self.sse_status_has_completed_loop(**kwargs)
        self.poller_result = all([self.sse_status_completed])
        return self.poller_result

    def sse_status_has_completed_loop(self, **kwargs):
        """Method to poll the status file for a server side export until it contains 'Completed'"""
        self._debug_locals(sys._getframe().f_code.co_name, locals())

        # loop counter
        self.loop_count = 1
        # establish a previous result_info that's empty
        self.previous_sse_status = ''

        while not self._stop:
            # get the SSE status
            self.sse_status = self.get_sse_status(**kwargs)

            # print a timing debug string
            if self.timeout:
                time_till_expiry = self.timeout - datetime.utcnow()
            else:
                time_till_expiry = 'Never'

            self.timing_str = (
                "Timing: Started: {}, Timeout: {}, Elapsed Time: {}, Left till expiry: {}, "
                "Loop Count: {}"
            ).format(
                self.start,
                self.timeout,
                datetime.utcnow() - self.start,
                time_till_expiry,
                self.loop_count,
            )
            self.progresslog.debug("{}{}".format(self.id_str, self.timing_str))

            # check to see if progress has changed, if so print progress log info
            progress_changed = any([
                self.previous_sse_status != self.sse_status,
            ])

            if progress_changed:
                m = "{}Progress Changed: '{}'".format
                self.progresslog.info(m(self.id_str, self.sse_status))

            if 'failed' in self.sse_status.lower():
                m = "{}Server Side Export Failed: '{}'".format
                raise pytan.exceptions.ServerSideExportError(m(self.id_str, self.sse_status))

            if 'completed' in self.sse_status.lower():
                m = "{}Server Side Export Completed: '{}'".format
                self.mylog.info(m(self.id_str, self.sse_status))
                return True

            # check to see if timeout is specified, if so and we have passed it, return
            # False
            if self.timeout and datetime.utcnow() >= self.timeout:
                m = "{}Reached timeout of {}".format
                self.mylog.warning(m(self.id_str, self.timeout))
                return False

            # if stop is called, return True
            if self._stop:
                m = "{}Stop called at {}".format
                self.mylog.info(m(self.id_str, self.sse_status))
                return False

            # update our class variables to the new values determined by this loop
            self.previous_sse_status = self.sse_status

            time.sleep(self.polling_secs)
            self.loop_count += 1
