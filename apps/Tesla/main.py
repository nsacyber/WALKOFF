import logging
from apps import App, action
import teslajson
import core.config.paths
import pyaes

logger = logging.getLogger(__name__)


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        device = self.get_device()

        self.connection = teslajson.Connection(device.username, device.get_password())

        try:
            self.vehicle = self.connection.vehicles[0]
        except IndexError:
            logger.error('This account has no tesla vehicles')

    @action
    def get_mobile_access(self):
        return bool(self.vehicle.data_request('mobile_enabled')['response'])

    # Functions relating to vehicle charge state
    @action
    def get_charge_state_all(self):
        return self.vehicle.data_request('charge_state')

    @action
    def get_charging_state(self):
        return (self.vehicle.data_request('charge_state'))['charging_state']

    @action
    def get_charge_to_max_range(self):
        return bool((self.vehicle.data_request('charge_state'))['charge_to_max_range'])

    @action
    def get_max_range_charge_counter(self):
        return int((self.vehicle.data_request('charge_state'))['max_range_charge_counter'])

    @action
    def get_fast_charger_present(self):
        return bool((self.vehicle.data_request('charge_state'))['fast_charger_present'])

    @action
    def get_battery_range(self):
        return float((self.vehicle.data_request('charge_state'))['battery_range'])

    @action
    def get_est_battery_range(self):
        return float((self.vehicle.data_request('charge_state'))['est_battery_range'])

    @action
    def get_ideal_battery_range(self):
        return float((self.vehicle.data_request('charge_state'))['ideal_battery_range'])

    @action
    def get_battery_level(self):
        return (self.vehicle.data_request('charge_state'))['battery_level']

    @action
    def get_battery_current(self):
        return (self.vehicle.data_request('charge_state'))['battery_current']

    # @action
    # def get_charge_starting_range(self):
    #     return (self.vehicle.data_request('charge_state'))['charge_starting_range']
    #
    # @action
    # def get_charge_starting_soc(self):
    #     return (self.vehicle.data_request('charge_state'))['charge_starting_soc']

    @action
    def get_charger_voltage(self):
        return float((self.vehicle.data_request('charge_state'))['charger_voltage'])

    @action
    def get_charger_pilot_current(self):
        return float((self.vehicle.data_request('charge_state'))['charger_pilot_current'])

    @action
    def get_charger_actual_current(self):
        return float((self.vehicle.data_request('charge_state'))['charger_actual_current'])

    @action
    def get_charger_power(self):
        return float((self.vehicle.data_request('charge_state'))['charger_power'])

    @action
    def get_time_to_full_charge(self):
        return (self.vehicle.data_request('charge_state'))['time_to_full_charge']

    @action
    def get_charge_rate(self):
        return float((self.vehicle.data_request('charge_state'))['charge_rate'])

    @action
    def get_charge_port_door_open(self):
        return bool((self.vehicle.data_request('charge_state'))['charge_port_door_open'])

    # Functions relating to vehicle climate state
    @action
    def get_climate_state_all(self):
        return self.vehicle.data_request('climate_state')

    @action
    def get_inside_temp(self):
        return float((self.vehicle.data_request('climate_state'))['inside_temp'])

    @action
    def get_outside_temp(self):
        return float((self.vehicle.data_request('climate_state'))['outside_temp'])

    @action
    def get_driver_temp_setting(self):
        return float((self.vehicle.data_request('climate_state'))['driver_temp_setting'])

    @action
    def get_passenger_temp_setting(self):
        return float((self.vehicle.data_request('climate_state'))['passenger_temp_setting'])

    @action
    def get_is_auto_conditioning_on(self):
        return bool((self.vehicle.data_request('climate_state'))['is_auto_conditioning_on'])

    @action
    def get_is_front_defroster_on(self):
        return bool((self.vehicle.data_request('climate_state'))['is_front_defroster_on'])

    @action
    def get_is_rear_defroster_on(self):
        return bool((self.vehicle.data_request('climate_state'))['is_rear_defroster_on'])

    @action
    def get_fan_status(self):
        return int((self.vehicle.data_request('climate_state'))['fan_status'])

    # Functions relating to vehicle driving and position
    @action
    def get_driving_and_position_all(self):
        return self.vehicle.data_request('drive_state')

    @action
    def get_shift_state(self):
        return (self.vehicle.data_request('driver_state'))['shift_state']

    @action
    def get_speed(self):
        return float((self.vehicle.data_request('driver_state'))['speed'])

    @action
    def get_latitude(self):
        return float((self.vehicle.data_request('driver_state'))['latitude'])

    @action
    def get_longitude(self):
        return float((self.vehicle.data_request('driver_state'))['longitude'])

    @action
    def get_heading(self):
        return int((self.vehicle.data_request('driver_state'))['heading'])

    # @action
    # def get_gps_as_of(self):
    #     return int((self.vehicle.data_request('driver_state'))['gps_as_of'])

    # Functions relating to vehicle GUI
    @action
    def get_gui_settings_all(self):
        return self.vehicle.data_request('gui_settings')

    @action
    def get_gui_distance_units(self):
        return (self.vehicle.data_request('gui_settings'))['gui_distance_units']

    @action
    def get_gui_temperature_units(self):
        return (self.vehicle.data_request('gui_settings'))['gui_temperature_units']

    @action
    def get_gui_charge_rate_units(self):
        return (self.vehicle.data_request('gui_settings'))['gui_charge_rate_units']

    @action
    def get_gui_24_hour_time(self):
        return bool((self.vehicle.data_request('gui_settings'))['gui_24_hour_time'])

    @action
    def get_gui_range_display(self):
        return (self.vehicle.data_request('gui_settings'))['gui_range_display']

    # Functions relating to vehicle state (mainly physical)
    @action
    def get_vehicle_state_all(self):
        return self.vehicle.data_request('vehicle_state')

    @action
    def get_driver_front_door(self):
        return bool((self.vehicle.data_request('vehicle_state'))['df'])

    @action
    def get_driver_rear_door(self):
        return bool((self.vehicle.data_request('vehicle_state'))['dr'])

    @action
    def get_passenger_front_door(self):
        return bool((self.vehicle.data_request('vehicle_state'))['pf'])

    @action
    def get_passenger_rear_door(self):
        return bool((self.vehicle.data_request('vehicle_state'))['pr'])

    @action
    def get_front_trunk(self):
        return bool((self.vehicle.data_request('vehicle_state'))['ft'])

    @action
    def get_rear_trunk(self):
        return bool((self.vehicle.data_request('vehicle_state'))['rt'])

    @action
    def get_car_firmware_version(self):
        return (self.vehicle.data_request('vehicle_state'))['car_version']

    @action
    def get_locked(self):
        return bool((self.vehicle.data_request('vehicle_state'))['locked'])

    @action
    def get_sunroof_installed(self):
        return bool((self.vehicle.data_request('vehicle_state'))['sun_roof_installed'])

    @action
    def get_sunroof_state(self):
        return (self.vehicle.data_request('vehicle_state'))['sun_roof_state']

    @action
    def get_sunroof_percent_open(self):
        return float((self.vehicle.data_request('vehicle_state'))['sun_roof_percent_open'])

    @action
    def get_dark_rims(self):
        return bool((self.vehicle.data_request('vehicle_state'))['dark_rims'])

    @action
    def get_wheel_type(self):
        return (self.vehicle.data_request('vehicle_state'))['wheel_type']

    @action
    def get_has_spoiler(self):
        return bool((self.vehicle.data_request('vehicle_state'))['has_spoiler'])

    @action
    def get_roof_color(self):
        return (self.vehicle.data_request('vehicle_state'))['roof_color']

    @action
    def get_perf_config(self):
        return (self.vehicle.data_request('vehicle_state'))['perf_config']

    @action
    def wake_up(self):
        return bool(self.vehicle.wake_up()['result'])

    @action
    def set_valet_mode(self, on, pin):
        # Args: boolean to disable or enable valet mode 'on', and 4 digit PIN to unlock the car 'password'
        data = {'mode': on}
        if pin is not None:
            data['password'] = pin
        return bool(self.vehicle.command('set_valet_mode', data=data)['result'])

    @action
    def reset_valet_pin(self):
        return bool(self.vehicle.command('reset_valet_pin'))

    @action
    def open_charge_port(self):
        return bool(self.vehicle.command('charge_port_door_open')['result'])

    @action
    def set_charge_limit_std(self):
        return bool(self.vehicle.command('charge_standard')['result'])

    @action
    def set_charge_limit_max_range(self):
        return bool(self.vehicle.command('charge_max_range')['result'])

    @action
    def set_charge_limit(self, limit):
        # Args: int percentage value for charge limit 'limit_value'
        data = {"limit_value": limit}
        return bool(self.vehicle.command('set_charge_limit', data=data)['result'])

    @action
    def start_charging(self):
        return bool(self.vehicle.command('charge_start')['result'])

    @action
    def stop_charging(self):
        return bool(self.vehicle.command('charge_stop')['result'])

    @action
    def flash_lights(self):
        return bool(self.vehicle.command('flash_lights')['result'])

    @action
    def honk_horn(self):
        return bool(self.vehicle.command('honk_horn')['result'])

    @action
    def unlock_doors(self):
        return bool(self.vehicle.command('door_unlock')['result'])

    @action
    def lock_doors(self):
        return bool(self.vehicle.command('door_lock')['result'])

    @action
    def set_temperature(self, driver_deg_c, passenger_deg_c):
        # Args: int temp for driver's side in celsius driver_degC, int temp for passenger's side in celsius pass_degC
        data = {"driver_degC": driver_deg_c, "pass_degC": passenger_deg_c}
        return bool(self.vehicle.command('set_temps', data=data)['result'])

    @action
    def start_hvac_system(self):
        return bool(self.vehicle.command('auto_conditioning_start')['result'])

    @action
    def stop_hvac_system(self):
        return bool(self.vehicle.command('auto_conditioning_stop')['result'])

    @action
    def move_pano_roof(self, state, percent):
        # Args: desired state of pano roof (open, close, comfort, vent) 'state', optional int percentage to move
        # the roof to 'percent'
        data = {"state": state, "percent": percent}
        return bool(self.vehicle.command('sun_roof_control', data=data)['result'])

    @action
    def remote_start(self):
        # Args: password to the account
        return bool(self.vehicle.command('remote_start_drive',
                                    data={"password": self.get_device().get_password()})['result'])

    # @action
    # def open_trunk(self):
    #     # Currently inoperable
    #     return self.vehicle.command('trunk_open', data={'which_trunk': 'rear'})['result'])
