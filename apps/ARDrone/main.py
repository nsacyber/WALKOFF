from apps import App, action
from apps.ARDrone.libardrone import libardrone
from time import sleep


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.drone = libardrone.ARDrone()

    @action
    def takeoff(self):
        """Make the drone takeoff."""
        self.drone.takeoff()

    @action
    def land(self):
        """Make the drone land."""
        self.drone.land()

    @staticmethod
    def __timed_execute(time):
        """ sleep for a given amount of time if time is > 0. Time is given im milliseconds"""
        if time >= 0:
            sleep(time/1000.)

    @action
    def hover(self, millisec):
        """Make the drone hover."""
        self.drone.at(libardrone.at_pcmd, False, 0, 0, 0, 0)
        self.__timed_execute(millisec)

    @action
    def move_left(self, speed, millisec):
        """Make the drone move left."""
        self.drone.at(libardrone.at_pcmd, True, -speed/10., 0, 0, 0)
        self.__timed_execute(millisec)

    @action
    def move_right(self, speed, millisec):
        """Make the drone move right."""
        self.drone.at(libardrone.at_pcmd, True, speed/10., 0, 0, 0)
        self.__timed_execute(millisec)

    @action
    def move_up(self, speed, millisec):
        """Make the drone rise upwards."""
        self.drone.at(libardrone.at_pcmd, True, 0, 0, speed/10., 0)
        self.__timed_execute(millisec)

    @action
    def move_down(self, speed, millisec):
        """Make the drone decent downwards."""
        self.drone.at(libardrone.at_pcmd, True, 0, 0, -speed/10., 0)
        self.__timed_execute(millisec)

    @action
    def move_forward(self, speed, millisec):
        """Make the drone move forward."""
        self.drone.at(libardrone.at_pcmd, True, 0, -speed/10., 0, 0)
        self.__timed_execute(millisec)

    @action
    def move_backward(self, speed, millisec):
        """Make the drone move backwards."""
        self.drone.at(libardrone.at_pcmd, True, 0, speed/10., 0, 0)
        self.__timed_execute(millisec)

    @action
    def turn_left(self, speed, millisec):
        """Make the drone rotate left."""
        self.drone.at(libardrone.at_pcmd, True, 0, 0, 0, -speed/10.)
        self.__timed_execute(millisec)

    @action
    def turn_right(self, speed, millisec):
        """Make the drone rotate right."""
        self.drone.at(libardrone.at_pcmd, True, 0, 0, 0, speed/10.)
        self.__timed_execute(millisec)

    @action
    def reset(self):
        """Toggle the drone's emergency state."""
        self.drone.reset()

    @action
    def trim(self):
        """Flat trim the drone."""
        self.drone.at(libardrone.at_ftrim)

    @action
    def set_speed(self, speed):
        """Set the drone's speed.

        Valid values are ints from [0.1]
        """
        self.drone.speed = speed/10.

    @action
    def move(self, left_right_tilt, front_back_tilt, vertical_speed, angular_speed, millisec):
        """Makes the drone move (translate/rotate).

       Parameters:
       lr -- left-right tilt: float [-1..1] negative: left, positive: right
       rb -- front-back tilt: float [-1..1] negative: forwards, positive:
            backwards
       vv -- vertical speed: float [-1..1] negative: go down, positive: rise
       va -- angular speed: float [-1..1] negative: spin left, positive: spin 
            right"""
        self.drone.at(libardrone.at_pcmd,
                      True,
                      left_right_tilt,
                      front_back_tilt,
                      vertical_speed,
                      angular_speed)
        self.__timed_execute(millisec)

    @action
    def halt(self):
        self.drone.halt()

    @action
    def get_image(self):
        return self.drone.image

    @action
    def get_battery(self):
        return str(self.drone.navdata.get(0, dict()).get('battery', 0))

    @action
    def get_theta(self):
        return str(self.drone.navdata.get(0, dict()).get('theta', 0))

    @action
    def get_phi(self):
        return str(self.drone.navdata.get(0, dict()).get('phi', 0))

    @action
    def get_psi(self):
        return str(self.drone.navdata.get(0, dict()).get('psi', 0))

    @action
    def get_altitude(self):
        return str(self.drone.navdata.get(0, dict()).get('altitude', 0))

    @action
    def get_velocity_x(self):
        return str(self.drone.navdata.get(0, dict()).get('vx', 0))

    @action
    def get_velocity_y(self):
        return str(self.drone.navdata.get(0, dict()).get('vy', 0))

    @action
    def get_velocity_z(self):
        return str(self.drone.navdata.get(0, dict()).get('vz', 0))

    def shutdown(self):
        self.drone.land()
        self.drone.halt()


