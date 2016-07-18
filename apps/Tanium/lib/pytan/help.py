# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
"""Provides methods for the :mod:`pytan` module to print help."""
import sys

# disable python from creating .pyc files everywhere
sys.dont_write_bytecode = True

import os

my_file = os.path.abspath(__file__)
my_dir = os.path.dirname(my_file)
parent_dir = os.path.dirname(my_dir)
path_adds = [parent_dir]
[sys.path.insert(0, aa) for aa in path_adds if aa not in sys.path]

import pytan


def passmein(func):
    """Decorator method to pass the function to a function that uses this decorator"""
    def wrapper(*args, **kwargs):
        return func(func, *args, **kwargs)
    return wrapper


@passmein
def sensors_help(me):
    """
Sensors Help
============

Supplying sensors controls what columns will be showed when you ask a
question.

A sensor string is a human string that describes, at a minimum, a sensor.
It can also optionally define a selector for the sensor, parameters for
the sensor, a filter for the sensor, and options for the filter for the
sensor. Sensors can be provided as a string or a list of strings.

Examples for basic sensors
---------------------------------

Supplying a single sensor:

    'Computer Name'

Supplying two sensors in a list of strings:

    ['Computer Name', 'IP Route Details']

Supplying multiple sensors with selectors (name is the default
selector if none is supplied):

    [
        'Computer Name',
        'name:Computer Name',
        'id:1',
        'hash:123456789',
    ]

Sensor Parameters
-----------------

Supplying parameters to a sensor can control the arguments that are
supplied to a sensor, if that sensor takes any arguments.

Sensor parameters must be surrounded with curly braces '{}',
and must have a key and value specified that is separated by
an equals '='. Multiple parameters must be seperated by
a comma ','. The key should match up to a valid parameter key
for the sensor in question.

If a parameter is supplied and the sensor doesn't have a
corresponding key name, it will be ignored. If the sensor has
parameters and a parameter is NOT supplied then one of two
paths will be taken:

    * if the parameter does not require a default value, the
    parameter is left blank and not supplied.
    * if the parameter does require a value (pulldowns, for
    example), a default value is derived (for pulldowns,
    the first value available as a pulldown entry is used).

Examples for sensors with parameters
------------------------------------

Supplying a single sensor with a single parameter 'dirname':

    'Sensor With Params{dirname=Program Files}'

Supplying a single sensor with two parameters, 'param1' and
'param2':

    'Sensor With Params{param1=value1,param2=value2}'

Sensor Filters
--------------

Supplying a filter to a sensor controls what data will be shown in
those columns (sensors) you've provided.

Sensor filters can be supplied by adding ', that FILTER:VALUE',
where FILTER is a valid filter string, and VALUE is the string
that you want FILTER to match on.

See filter help for a list of all possible FILTER strings.

See options help for a list of options that can control how
the filter works.

Examples for sensors with filters
---------------------------------

Supplying a sensor with a filter that limits the results to only
show column data that matches the regular expression
'.*Windows.*' (Tanium does a case insensitive match by default):

    'Computer Name, that contains:Windows'

Supplying a sensor with a filter that limits the results to only
show column data that matches the regular expression
'Microsoft.*':

    'Computer Name, that starts with:Microsoft'

Supply a sensor with a filter that limits the results to only
show column data that has a version greater or equal to
'39.0.0.0'. Since this sensor uses Version as its default result
type, there is no need to change the value type using filter
options.

    'Installed Application Version' \\
    '{Application Name=Google Chrome}, that =>:39.0.0.0'

Sensor Options
--------------

Supplying options to a sensor can change how the filter for
that sensor works.

Sensor options can be supplied by adding ', opt:OPTION' or
', opt:OPTION:VALUE' for those options that require values,
where OPTION is a valid option string, and VALUE is the
appropriate value required by accordant OPTION.

See options help for a list of options that can control how
the filter works.

Examples for sensors with options
---------------------------------

Supplying a sensor with an option that forces tanium to
re-fetch any cached column data that is older than 1 minute:

    'Computer Name, opt:max_data_age:60'

Supplying a sensor with filter and an option that causes
Tanium to match case for the filter value:

    'Computer Name, that contains:Windows, opt:match_case'

Supplying a sensor with a filter and an option that causes
Tanium to match all values supplied:

    'Computer Name, that contains:Windows, opt:match_all_values'

Supplying a sensor with a filter and a set of options that
causes Tanium to recognize the value type as String (which is
the default type for most sensors), re-fetch data older than
10 minutes, match any values, and match case:

    'Computer Name', that contains:Windows, ' \\
    opt:value_type:string, opt:max_data_age:600, ' \\
    'opt:match_any_value, opt:match_case'
"""
    return me.__doc__


@passmein
def package_help(me):
    """
Package Help
============

Supplying package defines what package will be deployed as part of the
action.

A package string is a human string that describes, at a minimum, a
package. It can also optionally define a selector for the package,
and/or parameters for the package. A package must be provided as a string.

Examples for package
---------------------------------

Supplying a package:

    'Distribute Tanium Standard Utilities'

Supplying a package by id:

    'id:1'

Supplying a package by hash:

    'hash:123456789'

Supplying a package by name:

    'name:Distribute Tanium Standard Utilities'

Package Parameters
------------------

Supplying parameters to a package can control the arguments
that are supplied to a package, if that package takes any arguments.

Package parameters must be surrounded with curly braces '{}',
and must have a key and value specified that is separated by
an equals '='. Multiple parameters must be seperated by
a comma ','. The key should match up to a valid parameter key
for the package in question.

If a parameter is supplied and the package doesn't have a
corresponding key name, it will be ignored. If the package has
parameters and a parameter is NOT supplied then an exception
will be raised, printing out the JSON of the missing paramater
for the package in question.

Examples for package with parameters
------------------------------------

Supplying a package with a single parameter '$1':

    'Package With Params{$1=value1}'

Supplying a package with two parameters, '$1' and '$2':

    'Package With Params{$1=value1,$2=value2}'
"""
    return me.__doc__


@passmein
def filters_help(me):
    """
Filters Help
============

Filters are used generously throughout pytan. When used as part of a
sensor string, they control what data is shown for the columns that
the sensor returns. When filters are used for whole question filters,
they control what rows will be returned. They are used by Groups to
define group membership, deploy actions to determine which machines
should have the action deployed to it, and more.

A filter string is a human string that describes, a sensor followed
by ', that FILTER:VALUE', where FILTER is a valid filter string,
and VALUE is the string that you want FILTER to match on.

Valid Filters
-------------

"""
    for x in pytan.constants.FILTER_MAPS:
        for y in x['human']:
            me.__doc__ += '    {!r:<25}\n'.format(y)
            me.__doc__ += '        Help: {}\n'.format(x['help'])
            me.__doc__ += '        Example: "Sensor1, that {}:VALUE"\n\n'.format(y)
    return me.__doc__


@passmein
def options_help(me):
    """
Options Help
============

Options are used for controlling how filters act. When options are
used as part of a sensor string, they change how the filters
supplied as part of that sensor operate. When options are used for
whole question options, they change how all of the question filters
operate.

When options are supplied for a sensor string, they must be
supplied as ', opt:OPTION' or ', opt:OPTION:VALUE' for options
that require a value.

When options are supplied for question options, they must be
supplied as 'OPTION' or 'OPTION:VALUE' for options that require
a value.

Options can be used on 'filter' or 'group', where 'group' pertains
to group filters or question filters. All 'filter' options are also
applicable to 'group' for question options.

Valid Options
-------------

"""
    for x in pytan.constants.OPTION_MAPS:
        me.__doc__ += '    {!r:<25}\n'.format(x['human'])
        me.__doc__ += '        Help: {}\n'.format(x['help'])

        me.__doc__ += '        Usable on: {}\n'.format(x['destination'])
        if x.get('human_type', ''):
            me.__doc__ += '        VALUE description and type: {}, {}\n'.format(
                x['human_type'], x['valid_type'])
            me.__doc__ += '        Example for sensor: "Sensor1, opt:{}:{}"\n'.format(
                x['human'], x['human_type'])
            me.__doc__ += '        Example for question: "{}:{}"\n'.format(
                x['human'], x['human_type'])
        else:
            me.__doc__ += '        Example for sensor: "Sensor1, opt:{}"\n'.format(x['human'])
            me.__doc__ += '        Example for question: "{}"\n'.format(x['human'])
        me.__doc__ += '\n'
    return me.__doc__
