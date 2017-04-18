from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED
from tests.util.servertestcase import ServerTestCase


class TestSchedulerActions(ServerTestCase):

    def test_scheduler_actions(self):
        self.post_with_status_check('/execution/scheduler/start', STATE_RUNNING, headers=self.headers)
        self.post_with_status_check('/execution/scheduler/start', "Scheduler already running.", headers=self.headers)

        self.post_with_status_check('/execution/scheduler/pause', STATE_PAUSED, headers=self.headers)
        self.post_with_status_check('/execution/scheduler/pause', "Scheduler already paused.", headers=self.headers)

        self.post_with_status_check('/execution/scheduler/resume', STATE_RUNNING, headers=self.headers)
        self.post_with_status_check('/execution/scheduler/resume',
                                    "Scheduler is not in PAUSED state and cannot be resumed.", headers=self.headers)

        self.post_with_status_check('/execution/scheduler/stop', STATE_STOPPED, headers=self.headers)
        self.post_with_status_check('/execution/scheduler/stop', "Scheduler already stopped.", headers=self.headers)
