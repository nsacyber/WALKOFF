from server import appdevice
import teslajson


# There is an associated Hello world test workflow which can be executed
class Main(appdevice.App):
    def __init__(self, name=None, device=None):
        # The parent app constructor looks for a device configuration and returns that as a dict called self.config
        appdevice.App.__init__(self, name, device)
        # Functions and Variables that are designed to exist across functions go here

    def initialize_connection(self, args={}):
        self.c = teslajson.Connection(args['email'], args['password'])
        self.vehicle = self.c.vehicles[0]

    def get_mobile_access(self):
        return self.vehicle.data_request('mobile_enabled')

    # Functions relating to vehicle charge state
    def get_charge_state_all(self):
        return self.vehicle.data_request('charge_state')

    def get_charging_state(self):
        return (self.vehicle.data_request('charge_state'))['charging_state']

    def get_charge_to_max_range(self):
        return (self.vehicle.data_request('charge_state'))['charge_to_max_range']

    def get_max_range_charge_counter(self):
        return (self.vehicle.data_request('charge_state'))['max_range_charge_counter']

    def get_fast_charger_present(self):
        return (self.vehicle.data_request('charge_state'))['fast_charger_present']

    def get_battery_range(self):
        return (self.vehicle.data_request('charge_state'))['battery_range']

    def get_est_battery_range(self):
        return (self.vehicle.data_request('charge_state'))['est_battery_range']

    def get_ideal_battery_range(self):
        return (self.vehicle.data_request('charge_state'))['ideal_battery_range']

    def get_battery_level(self):
        return (self.vehicle.data_request('charge_state'))['battery_level']

    def get_battery_current(self):
        return (self.vehicle.data_request('charge_state'))['battery_current']

    def get_charge_starting_range(self):
        return (self.vehicle.data_request('charge_state'))['charge_starting_range']

    def get_charge_starting_soc(self):
        return (self.vehicle.data_request('charge_state'))['charge_starting_soc']

    def get_charger_voltage(self):
        return (self.vehicle.data_request('charge_state'))['charger_voltage']

    def get_charger_pilot_current(self):
        return (self.vehicle.data_request('charge_state'))['charger_pilot_current']

    def get_charger_actual_current(self):
        return (self.vehicle.data_request('charge_state'))['charger_actual_current']

    def get_charger_power(self):
        return (self.vehicle.data_request('charge_state'))['charger_power']

    def get_time_to_full_charge(self):
        return (self.vehicle.data_request('charge_state'))['time_to_full_charge']

    def get_charge_rate(self):
        return (self.vehicle.data_request('charge_state'))['charge_rate']

    def get_charge_port_door_open(self):
        return (self.vehicle.data_request('charge_state'))['charge_port_door_open']

    # Functions relating to vehicle climate state
    def get_climate_state_all(self):
        return self.vehicle.data_request('climate_state')

    def get_inside_temp(self):
        return (self.vehicle.data_request('climate_state'))['inside_temp']

    def get_outside_temp(self):
        return (self.vehicle.data_request('climate_state'))['outside_temp']

    def get_driver_temp_setting(self):
        return (self.vehicle.data_request('climate_state'))['driver_temp_setting']

    def get_passenger_temp_setting(self):
        return (self.vehicle.data_request('climate_state'))['passenger_temp_setting']

    def get_is_auto_conditioning_on(self):
        return (self.vehicle.data_request('climate_state'))['is_auto_conditioning_on']

    def get_is_front_defroster_on(self):
        return (self.vehicle.data_request('climate_state'))['is_front_defroster_on']

    def get_is_rear_defroster_on(self):
        return (self.vehicle.data_request('climate_state'))['is_rear_defroster_on']

    def get_fan_status(self):
        return (self.vehicle.data_request('climate_state'))['fan_status']

    # Functions relating to vehicle driving and position
    def get_driving_and_position_all(self):
        return self.vehicle.data_request('drive_state')

    def get_shift_state(self):
        return (self.vehicle.data_request('driver_state'))['shift_state']

    def get_speed(self):
        return (self.vehicle.data_request('driver_state'))['speed']

    def get_latitude(self):
        return (self.vehicle.data_request('driver_state'))['latitude']

    def get_longitude(self):
        return (self.vehicle.data_request('driver_state'))['longitude']

    def get_heading(self):
        return (self.vehicle.data_request('driver_state'))['heading']

    def get_gps_as_of(self):
        return (self.vehicle.data_request('driver_state'))['gps_as_of']

    # Functions relating to vehicle GUI
    def get_gui_settings_all(self):
        return self.vehicle.data_request('gui_settings')

    def get_gui_distance_units(self):
        return (self.vehicle.data_request('gui_settings'))['gui_distance_units']

    def get_gui_temperature_units(self):
        return (self.vehicle.data_request('gui_settings'))['gui_temperature_units']

    def get_gui_charge_rate_units(self):
        return (self.vehicle.data_request('gui_settings'))['gui_charge_rate_units']

    def get_gui_24_hour_time(self):
        return (self.vehicle.data_request('gui_settings'))['gui_24_hour_time']

    def get_gui_range_display(self):
        return (self.vehicle.data_request('gui_settings'))['gui_range_display']

    # Functions relating to vehicle state (mainly physical)
    def get_vehicle_state_all(self):
        return self.vehicle.data_request('vehicle_state')

    def get_driver_front_door(self):
        return (self.vehicle.data_request('vehicle_state'))['df']

    def get_driver_rear_door(self):
        return (self.vehicle.data_request('vehicle_state'))['dr']

    def get_passenger_front_door(self):
        return (self.vehicle.data_request('vehicle_state'))['pf']

    def get_passenger_rear_door(self):
        return (self.vehicle.data_request('vehicle_state'))['pr']

    def get_front_trunk(self):
        return (self.vehicle.data_request('vehicle_state'))['ft']

    def get_rear_trunk(self):
        return (self.vehicle.data_request('vehicle_state'))['rt']

    def get_car_firmware_version(self):
        return (self.vehicle.data_request('vehicle_state'))['car_version']

    def get_locked(self):
        return (self.vehicle.data_request('vehicle_state'))['locked']

    def get_sun_roof_installed(self):
        return (self.vehicle.data_request('vehicle_state'))['sun_roof_installed']

    def get_sun_roof_state(self):
        return (self.vehicle.data_request('vehicle_state'))['sun_roof_state']

    def get_sun_roof_percent_open(self):
        return (self.vehicle.data_request('vehicle_state'))['sun_roof_percent_open']

    def get_dark_rims(self):
        return (self.vehicle.data_request('vehicle_state'))['dark_rims']

    def get_wheel_type(self):
        return (self.vehicle.data_request('vehicle_state'))['wheel_type']

    def get_has_spoiler(self):
        return (self.vehicle.data_request('vehicle_state'))['has_spoiler']

    def get_roof_color(self):
        return (self.vehicle.data_request('vehicle_state'))['roof_color']

    def get_perf_config(self):
        return (self.vehicle.data_request('vehicle_state'))['perf_config']

    def wake_up(self):
        return self.vehicle.wake_up()

    def set_valet_mode(self, args={}):
        # Args: boolean to disable or enable valet mode 'on', and 4 digit PIN to unlock the car 'password'
        return self.vehicle.command('set_valet_mode', args)

    def reset_valet_pin(self, args={}):
        return self.vehicle.command('reset_valet_pin')

    def open_charge_port(self):
        return self.vehicle.command('charge_port_door_open')

    def set_charge_limit_std(self):
        return self.vehicle.command('charge_standard')

    def set_charge_limit_max_range(self):
        return self.vehicle.command('charge_max_range')

    def set_charge_limit(self, args={}):
        # Args: int percentage value for charge limit 'limit_value'
        return self.vehicle.command('set_charge_limit', data=args)

    def start_charging(self):
        return self.vehicle.command('charge_start')

    def stop_charging(self):
        return self.vehicle.command('charge_stop')

    def flash_lights(self):
        return self.vehicle.command('flash_lights')

    def honk_horn(self):
        return self.vehicle.command('honk_horn')

    def unlock_doors(self):
        return self.vehicle.command('door_unlock')

    def lock_doors(self):
        return self.vehicle.command('door_lock')

    def set_temperature(self, args={}):
        # Args: int temp for driver's side in celsius driver_degC, int temp for passenger's side in celsius pass_degC
        return self.vehicle.command('set_temps', data=args)

    def start_HVAC_system(self):
        return self.vehicle.command('auto_conditioning_start')

    def stop_HVAC_system(self):
        return self.vehicle.command('auto_conditioning_stop')

    def move_pano_roof(self, args={}):
        # Args: desired state of pano roof (open, close, comfort, vent) 'state', optional int percentage to move
        # the roof to 'percent'
        return self.vehicle.command('sun_roof_control', data=args)

    def remote_start(self, args={}):
        # Args: password to the account
        return self.vehicle.command('remote_start_drive', data=args)

    def open_trunk(self):
        # Currently inoperable
        return self.vehicle.command('trunk_open', data={'which_trunk': 'rear'})

    def shutdown(self):
        return
