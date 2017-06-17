import unittest
from core.flag import Flag
from core.step import Step, _Widget
from core.nextstep import NextStep
import core.config.config
import core.config.paths
from tests.config import test_apps_path, function_api_path
from core.instance import Instance
from core.helpers import (import_all_apps, UnknownApp, UnknownAppAction, InvalidInput, import_all_flags,
                          import_all_filters)


class TestStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def setUp(self):
        self.basic_json = {'app': 'HelloWorld',
                           'action': 'helloWorld',
                           'device': '',
                           'name': '',
                           'next': [],
                           'errors': [],
                           'position': {},
                           'input': {},
                           'widgets': [],
                           'risk': 0}
        self.basic_input_json = {'app': 'HelloWorld',
                                 'action': 'helloWorld',
                                 'name': '',
                                 'next': [],
                                 'errors': [],
                                 'position': {},
                                 'input': {}}

    def __compare_init(self, elem, name, parent_name, action, app, device, inputs, next_steps, errors, ancestry,
                       widgets, risk=0., position=None):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.parent_name, parent_name)
        self.assertEqual(elem.action, action)
        self.assertEqual(elem.app, app)
        self.assertEqual(elem.device, device)
        self.assertDictEqual({key: input_element for key, input_element in elem.input.items()}, inputs)
        self.assertListEqual([conditional.as_json() for conditional in elem.conditionals], next_steps)
        self.assertListEqual([error.as_json() for error in elem.errors], errors)
        self.assertListEqual(elem.ancestry, ancestry)
        self.assertEqual(elem.risk, risk)
        widgets = [_Widget(app, widget) for (app, widget) in widgets]
        self.assertEqual(len(elem.widgets), len(widgets))
        for widget in elem.widgets:
            self.assertIn(widget, widgets)
        position = position if position is not None else {}
        self.assertDictEqual(elem.position, position)
        self.assertIsNone(elem.output)
        self.assertFalse(elem.templated)

    def test_init_app_and_action_only(self):
        step = Step(app='HelloWorld', action='helloWorld')
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], [])

    def test_init_app_and_action_name_different_than_method_name(self):
        step = Step(app='HelloWorld', action='Hello World')
        self.__compare_init(step, '', '', 'Hello World', 'HelloWorld', '', {}, [], [], ['', ''], [])

    def test_init_invalid_app(self):
        with self.assertRaises(UnknownApp):
            Step(app='InvalidApp', action='helloWorld')

    def test_init_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            Step(app='HelloWorld', action='invalid')

    def test_init_with_inputs_no_conversion(self):
        step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': -5.6})
        self.__compare_init(step, '', '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6}, [], [], ['', ''], [])

    def test_init_with_inputs_with_conversion(self):
        step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': '-5.6'})
        self.__compare_init(step, '', '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6}, [], [], ['', ''], [])

    def test_init_with_invalid_input_name(self):
        with self.assertRaises(InvalidInput):
            Step(app='HelloWorld', action='returnPlusOne', inputs={'invalid': '-5.6'})

    def test_init_with_invalid_input_type(self):
        with self.assertRaises(InvalidInput):
            Step(app='HelloWorld', action='returnPlusOne', inputs={'number': 'invalid'})

    def test_init_with_name(self):
        step = Step(app='HelloWorld', action='helloWorld', name='name')
        self.__compare_init(step, 'name', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', 'name'], [])

    def test_init_with_name_and_parent_name(self):
        step = Step(app='HelloWorld', action='helloWorld', name='name', parent_name='parent')
        self.__compare_init(step, 'name', 'parent', 'helloWorld', 'HelloWorld', '', {}, [], [], ['parent', 'name'], [])

    def test_init_with_name_and_parent_name_and_ancestry(self):
        step = Step(app='HelloWorld', action='helloWorld', name='name', parent_name='parent', ancestry=['a', 'b'])
        self.__compare_init(step, 'name', 'parent', 'helloWorld', 'HelloWorld', '', {}, [], [], ['a', 'b', 'name'], [])

    def test_init_with_device(self):
        step = Step(app='HelloWorld', action='helloWorld', device='dev')
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', 'dev', {}, [], [], ['', ''], [])

    def test_init_with_risk(self):
        step = Step(app='HelloWorld', action='helloWorld', risk=42.3)
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], [], risk=42.3)

    def test_init_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        step = Step(app='HelloWorld', action='helloWorld', widgets=widgets)
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], widgets)

    def test_init_with_position(self):
        step = Step(app='HelloWorld', action='helloWorld', position={'x': -12.3, 'y': 485})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], [],
                            position={'x': -12.3, 'y': 485})

    def test_init_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [step.as_json() for step in next_steps],
                            [], ['', ''], [])

    def test_init_with_error_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', errors=next_steps)
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [],
                            [step.as_json() for step in next_steps], ['', ''], [])

    def test_as_json_with_children(self):
        step = Step(app='HelloWorld', action='helloWorld')
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children(self):
        step = Step(app='HelloWorld', action='helloWorld')
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_with_children_with_name(self):
        step = Step(app='HelloWorld', action='helloWorld', name='name')
        self.basic_json['name'] = 'name'
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children_with_name(self):
        step = Step(app='HelloWorld', action='helloWorld', name='name')
        self.basic_json['name'] = 'name'
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_with_children_with_device(self):
        step = Step(app='HelloWorld', action='helloWorld', device='device')
        self.basic_json['device'] = 'device'
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children_with_device(self):
        step = Step(app='HelloWorld', action='helloWorld', device='device')
        self.basic_json['device'] = 'device'
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_with_children_with_risk(self):
        step = Step(app='HelloWorld', action='helloWorld', risk=120.6)
        self.basic_json['risk'] = 120.6
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children_with_risk(self):
        step = Step(app='HelloWorld', action='helloWorld', risk=169.5)
        self.basic_json['risk'] = 169.5
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_with_children_with_inputs(self):
        step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': '-5.6'})
        self.basic_json['action'] = 'returnPlusOne'
        self.basic_json['input'] = {'number': -5.6}
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children_with_inputs(self):
        step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': '-5.6'})
        self.basic_json['action'] = 'returnPlusOne'
        self.basic_json['input'] = {'number': -5.6}
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_without_children_with_input_routing(self):
        step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': '@step1'})
        self.basic_json['action'] = 'returnPlusOne'
        self.basic_json['input'] = {'number': '@step1'}
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_with_children_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        self.basic_json['next'] = [next_step.as_json() for next_step in next_steps]
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        self.basic_json['next'] = [next_step.name for next_step in next_steps]
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_with_children_with_error_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', errors=next_steps)
        self.basic_json['errors'] = [next_step.as_json() for next_step in next_steps]
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children_with_error_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', errors=next_steps)
        self.basic_json['errors'] = [next_step.name for next_step in next_steps]
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_with_children_with_position(self):
        step = Step(app='HelloWorld', action='helloWorld', position={'x': -12.3, 'y': 485})
        self.basic_json['position'] = {'x': -12.3, 'y': 485}
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children_with_position(self):
        step = Step(app='HelloWorld', action='helloWorld', position={'x': -12.3, 'y': 485})
        self.basic_json['position'] = {'x': -12.3, 'y': 485}
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def test_as_json_with_children_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        step = Step(app='HelloWorld', action='helloWorld', widgets=widgets)
        self.basic_json['widgets'] = [{'app': widget[0], 'name': widget[1]} for widget in widgets]
        self.assertDictEqual(step.as_json(with_children=True), self.basic_json)

    def test_as_json_without_children_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        step = Step(app='HelloWorld', action='helloWorld', widgets=widgets)
        self.basic_json['widgets'] = [{'app': widget[0], 'name': widget[1]} for widget in widgets]
        self.assertDictEqual(step.as_json(with_children=False), self.basic_json)

    def __check_xml(self, step,
                    app='HelloWorld',
                    action='helloWorld',
                    name='',
                    device='',
                    inputs=None,
                    next_steps=None,
                    errors=None,
                    position=None,
                    widgets=None,
                    risk=None):
        xml = step.to_xml()
        self.assertEqual(xml.tag, 'step')
        self.assertEqual(xml.get('id'), name)
        name_xml = xml.findall('name')
        self.assertEqual(len(name_xml), 1)
        self.assertEqual(name_xml[0].text, name)
        app_xml = xml.findall('app')
        self.assertEqual(len(app_xml), 1)
        self.assertEqual(app_xml[0].text, app)
        action_xml = xml.findall('action')
        self.assertEqual(len(action_xml), 1)
        self.assertEqual(action_xml[0].text, action)

        device_xml = xml.findall('device')
        if device:
            self.assertEqual(len(device_xml), 1)
            self.assertEqual(device_xml[0].text, device)
        else:
            self.assertEqual(len(device_xml), 0)

        inputs_xml = xml.findall('inputs')
        if inputs is not None:
            self.assertEqual(len(inputs_xml), 1)
            inputs_xml = xml.findall('inputs/*')
            self.assertEqual(len(inputs_xml), len(inputs))
            for input_xml in inputs_xml:
                self.assertIn(input_xml.tag, inputs.keys())
                self.assertEqual(input_xml.text, inputs[input_xml.tag])
        else:
            self.assertEqual(len(inputs_xml), 0)

        next_step_xml = xml.findall('next')
        if next_steps is not None:
            self.assertEqual(len(next_step_xml), len(next_steps))
        else:
            self.assertEqual(len(next_step_xml), 0)

        errors_xml = xml.findall('error')
        if errors is not None:
            self.assertEqual(len(errors_xml), len(errors))
        else:
            self.assertEqual(len(errors_xml), 0)

        position_xml = xml.findall('position')
        if position is not None:
            self.assertEqual(len(position_xml), 1)
            position_elements = position_xml[0].findall('*')
            self.assertEqual(len(position_elements), 2)
            x_position = position_xml[0].find('x')
            self.assertEqual(x_position.text, position['x'])
            y_position = position_xml[0].find('y')
            self.assertEqual(y_position.text, position['y'])
        else:
            self.assertEqual(len(position_xml), 0)

        widgets_xml = xml.findall('widgets')
        if widgets is not None:
            self.assertEqual(len(widgets_xml), 1)
            widgets_xml = widgets_xml[0].findall('*')
            self.assertEqual(len(widgets_xml), len(widgets))
            widget_ids = [(widget.get('app'), widget.text) for widget in widgets_xml]
            for widget in widget_ids:
                self.assertIn(widget, widgets)
        else:
            self.assertEqual(len(widgets_xml), 0)

        risk_xml = xml.findall('risk')
        if risk is not None:
            self.assertEqual(len(risk_xml), 1)
            self.assertEqual(risk_xml[0].text, risk)
        else:
            self.assertEqual(len(risk_xml), 0)

    def test_to_xml(self):
        step = Step(app='HelloWorld', action='helloWorld')
        self.__check_xml(step)

    def test_to_xml_with_name(self):
        step = Step(app='HelloWorld', action='helloWorld', name='name')
        self.__check_xml(step, name='name')

    def test_to_xml_with_device(self):
        step = Step(app='HelloWorld', action='helloWorld', device='device1')
        self.__check_xml(step, device='device1')

    def test_to_xml_with_device_empty_string(self):
        step = Step(app='HelloWorld', action='helloWorld', device='')
        self.__check_xml(step, device='')

    def test_to_xml_with_inputs(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '-10.265'})
        self.__check_xml(step, action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '-10.265'})

    def test_to_xml_with_inputs_with_routing(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '@step1', 'num3': '@step2'})
        self.__check_xml(step, action='Add Three', inputs={'num1': '-5.6', 'num2': '@step1', 'num3': '@step2'})

    def test_to_xml_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        self.__check_xml(step, next_steps=next_steps)

    def test_to_xml_with_error_steps(self):
        errors = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', errors=errors)
        self.__check_xml(step, errors=errors)

    def test_to_xml_with_position(self):
        step = Step(app='HelloWorld', action='helloWorld', position={'x': -12.3, 'y': 485})
        self.__check_xml(step, position={'x': '-12.3', 'y': '485'})

    def test_to_xml_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        step = Step(app='HelloWorld', action='helloWorld', widgets=widgets)
        self.__check_xml(step, widgets=widgets)

    def test_to_xml_with_risk(self):
        step = Step(app='HelloWorld', action='helloWorld', risk=27.6)
        self.__check_xml(step, risk=27.6)

    def __assert_xml_is_convertible(self, step):
        original_json = step.as_json()
        original_xml = step.to_xml()
        new_step = Step(xml=original_xml)
        self.assertDictEqual(new_step.as_json(), original_json)

    def test_to_from_xml(self):
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld'))

    def test_to_from_xml_with_name(self):
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld', name='name'))

    def test_to_from_xml_with_device(self):
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld', device='device1'))

    def test_to_from_xml_with_device_empty_string(self):
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld', device=''))

    def test_to_from_xml_with_inputs(self):
        self.__assert_xml_is_convertible(Step(app='HelloWorld',
                                              action='Add Three',
                                              inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '-10.265'}))

    def test_to_from_xml_with_complex_inputs(self):
        self.__assert_xml_is_convertible(Step(app='HelloWorld',
                                              action='Json Sample',
                                              inputs={'json_in': {'a': '-5.6', 'b': '4.3'}}))

    def test_to_from_xml_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld', next_steps=next_steps))

    def test_to_from_xml_with_error_steps(self):
        errors = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld', errors=errors))

    def test_to_from_xml_with_position(self):
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld',
                                              position={'x': '-12.3', 'y': '485'}))

    def test_to_from_xml_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld', widgets=widgets))

    def test_to_from_xml_with_risk(self):
        self.__assert_xml_is_convertible(Step(app='HelloWorld', action='helloWorld', risk=27.6))

    def test_from_json_app_and_action_only(self):
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], [])

    def test_from_json_invalid_app(self):
        self.basic_input_json['app'] = 'Invalid'
        with self.assertRaises(UnknownApp):
            Step.from_json(self.basic_input_json, {})

    def test_from_json_invalid_action(self):
        self.basic_input_json['action'] = 'invalid'
        with self.assertRaises(UnknownAppAction):
            Step.from_json(self.basic_input_json, {})

    def test_from_json__with_parent_name(self):
        step = Step.from_json(self.basic_input_json, {}, parent_name='parent')
        self.__compare_init(step, '', 'parent', 'helloWorld', 'HelloWorld', '', {}, [], [], ['parent', ''], [])

    def test_from_json_with_ancestry(self):
        step = Step.from_json(self.basic_input_json, {}, ancestry=['a', 'b'])
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['a', 'b', ''], [])

    def test_from_json_with_parent_name_and_ancestry(self):
        step = Step.from_json(self.basic_input_json, {}, parent_name='parent', ancestry=['a', 'b'])
        self.__compare_init(step, '', 'parent', 'helloWorld', 'HelloWorld', '', {}, [], [], ['a', 'b', ''], [])

    def test_from_json_with_name(self):
        self.basic_input_json['name'] = 'name1'
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, 'name1', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', 'name1'], [])

    def test_from_json_with_risk(self):
        self.basic_input_json['risk'] = 132.3
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], [], risk=132.3)

    def test_from_json_with_device(self):
        self.basic_input_json['device'] = 'device1'
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', 'device1', {}, [], [], ['', ''], [])

    def test_from_json_with_device_is_none(self):
        self.basic_input_json['device'] = None
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], [])

    def test_from_json_with_device_is_none_string(self):
        self.basic_input_json['device'] = 'None'
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], [])

    def test_from_json_with_widgets(self):
        widget_json = [{'name': 'widget_name', 'app': 'app1'}, {'name': 'w2', 'app': 'app2'}]
        widget_tuples = [('app1', 'widget_name'), ('app2', 'w2')]
        self.basic_input_json['widgets'] = widget_json
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], [], ['', ''], widget_tuples)

    def test_from_json_with_inputs(self):
        self.basic_input_json['action'] = 'Add Three'
        self.basic_input_json['input'] = {'num1': '-5.6', 'num2': '4.3', 'num3': '-10.265'}
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'Add Three', 'HelloWorld', '',
                            {'num1': -5.6, 'num2': 4.3, 'num3': -10.265}, [], [], ['', ''], [])

    def test_from_json_with_inputs_invalid_name(self):
        self.basic_input_json['action'] = 'Add Three'
        self.basic_input_json['input'] = {'num1': '-5.6', 'invalid': '4.3', 'num3': '-10.265'}
        with self.assertRaises(InvalidInput):
            Step.from_json(self.basic_input_json, {})

    def test_from_json_with_inputs_invalid_format(self):
        self.basic_input_json['action'] = 'Add Three'
        self.basic_input_json['input'] = {'num1': '-5.6', 'num2': '4.3', 'num3': 'invalid'}
        with self.assertRaises(InvalidInput):
            Step.from_json(self.basic_input_json, {})

    def test_from_json_with_step_routing(self):
        self.basic_input_json['action'] = 'Add Three'
        self.basic_input_json['input'] = {'num1': '-5.6', 'num2': '@step1', 'num3': '@step2'}
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'Add Three', 'HelloWorld', '',
                            {'num1': -5.6, 'num2': '@step1', 'num3': '@step2'}, [], [], ['', ''], [])

    def test_from_json_with_position(self):
        step = Step.from_json(self.basic_input_json, {'x': 125.3, 'y': 198.7})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '',
                            {}, [], [], ['', ''], [], position={'x': '125.3', 'y': '198.7'})

    def test_from_json_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        next_steps_json = [next_step.as_json() for next_step in next_steps]
        self.basic_input_json['next'] = next_steps_json
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, next_steps_json, [], ['', ''], [])

    def test_from_json_with_error_steps(self):
        error_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        error_steps_json = [next_step.as_json() for next_step in error_steps]
        self.basic_input_json['errors'] = error_steps_json
        step = Step.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', '', 'helloWorld', 'HelloWorld', '', {}, [], error_steps_json, ['', ''], [])

    def test_execute_no_args(self):
        step = Step(app='HelloWorld', action='helloWorld')
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        self.assertDictEqual(step.execute(instance.instance, {}), {'message': 'HELLO WORLD'})
        self.assertDictEqual(step.output, {'message': 'HELLO WORLD'})

    def test_execute_with_args(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        self.assertAlmostEqual(step.execute(instance.instance, {}), 8.9)
        self.assertAlmostEqual(step.output, 8.9)

    def test_execute_with_accumulator_with_conversion(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3'}
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        self.assertAlmostEqual(step.execute(instance.instance, accumulator), 8.9)
        self.assertAlmostEqual(step.output, 8.9)

    def test_execute_with_accumulator_with_extra_steps(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3', '3': '45'}
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        self.assertAlmostEqual(step.execute(instance.instance, accumulator), 8.9)
        self.assertAlmostEqual(step.output, 8.9)

    def test_execute_with_accumulator_missing_step(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(InvalidInput):
            step.execute(instance.instance, accumulator)

    def test_execute_with_complex_inputs(self):
        step = Step(app='HelloWorld', action='Json Sample', inputs={'json_in': {'a': '-5.6', 'b': '4.3'}})
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        self.assertAlmostEqual(step.execute(instance.instance, {}), -1.3)
        self.assertAlmostEqual(step.output, -1.3)

    def test_execute_action_which_raises_exception(self):
        from tests.apps.HelloWorld.exceptions import CustomException
        step = Step(app='HelloWorld', action='Buggy')
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(CustomException):
            step.execute(instance.instance, {})

    def test_get_next_step_no_next_steps_no_errors(self):
        step = Step(app='HelloWorld', action='helloWorld')
        step.output = 'something'
        self.assertIsNone(step.get_next_step({}))

    def test_get_next_step_error_no_next_steps_no_errors(self):
        step = Step(app='HelloWorld', action='helloWorld')
        step.output = 'something'
        self.assertIsNone(step.get_next_step({}, error=True))

    def test_get_next_step_no_errors(self):
        flag1 = [Flag(action='mod1_flag2', args={'arg1': '3'}), Flag(action='mod1_flag2', args={'arg1': '-1'})]
        next_steps = [NextStep(flags=flag1, name='name1'), NextStep(name='name2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        step.output = 2
        self.assertEqual(step.get_next_step({}), 'name2')
        step.output = 1
        self.assertEqual(step.get_next_step({}), 'name1')

    def test_get_next_step_with_errors(self):
        flag1 = [Flag(action='mod1_flag2', args={'arg1': '3'}), Flag(action='mod1_flag2', args={'arg1': '-1'})]
        flag2 = [Flag(action='mod1_flag2', args={'arg1': '-1'}), Flag(action='mod1_flag2', args={'arg1': '3'})]
        next_steps = [NextStep(flags=flag1, name='name1'), NextStep(name='name2')]
        error_steps = [NextStep(flags=flag2, name='error1'), NextStep(name='error2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps, errors=error_steps)
        step.output = 2
        self.assertEqual(step.get_next_step({}), 'name2')
        step.output = 1
        self.assertEqual(step.get_next_step({}), 'name1')

    def test_get_next_step_error_no_next_steps(self):
        flag1 = [Flag(action='mod1_flag2', args={'arg1': '3'}), Flag(action='mod1_flag2', args={'arg1': '-1'})]
        error_steps = [NextStep(flags=flag1, name='error1'), NextStep(name='error2')]
        step = Step(app='HelloWorld', action='helloWorld', errors=error_steps)
        step.output = 2
        self.assertEqual(step.get_next_step({}, error=True), 'error2')
        step.output = 1
        self.assertEqual(step.get_next_step({}, error=True), 'error1')

    def test_get_next_step_error_with_next_steps(self):
        flag1 = [Flag(action='mod1_flag2', args={'arg1': '3'}), Flag(action='mod1_flag2', args={'arg1': '-1'})]
        flag2 = [Flag(action='mod1_flag2', args={'arg1': '-1'}), Flag(action='mod1_flag2', args={'arg1': '3'})]
        next_steps = [NextStep(flags=flag1, name='name1'), NextStep(name='name2')]
        error_steps = [NextStep(flags=flag2, name='error1'), NextStep(name='error2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps, errors=error_steps)
        step.output = 2
        self.assertEqual(step.get_next_step({}, error=True), 'error2')
        step.output = 1
        self.assertEqual(step.get_next_step({}, error=True), 'error1')

    def test_get_children_no_ancestry(self):
        step = Step(app='HelloWorld', action='helloWorld')
        self.assertDictEqual(step.get_children([]), step.as_json(with_children=False))

    def test_get_children_next_not_found(self):
        next_steps = [NextStep(name='name1'), NextStep(name='name2')]
        error_steps = [NextStep(name='error1'), NextStep(name='error2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps, errors=error_steps)
        self.assertIsNone(step.get_children(['invalid']))

    def test_get_children_in_next_step(self):
        next_steps = [NextStep(name='name1'), NextStep(name='name2')]
        error_steps = [NextStep(name='error1'), NextStep(name='error2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps, errors=error_steps)
        self.assertDictEqual(step.get_children(['name1']), next_steps[0].as_json(with_children=False))
        self.assertDictEqual(step.get_children(['name2']), next_steps[1].as_json(with_children=False))

    def test_get_children_in_error(self):
        next_steps = [NextStep(name='name1'), NextStep(name='name2')]
        error_steps = [NextStep(name='error1'), NextStep(name='error2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps, errors=error_steps)
        self.assertDictEqual(step.get_children(['error1']), error_steps[0].as_json(with_children=False))
        self.assertDictEqual(step.get_children(['error2']), error_steps[1].as_json(with_children=False))

    def test_get_children_duplicate_in_both_next_steps_and_error(self):
        next_steps = [NextStep(name='name1'), NextStep(name='name2')]
        error_steps = [NextStep(name='name1'), NextStep(name='error2')]
        step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps, errors=error_steps)
        self.assertDictEqual(step.get_children(['name1']), next_steps[0].as_json(with_children=False))

    def test_name_parent_rename(self):
        step = Step(app='HelloWorld', action='helloWorld', ancestry=['step_parent'], name='step')
        new_ancestry = ['step_parent_update']
        step.reconstruct_ancestry(new_ancestry)
        new_ancestry.append('step')
        self.assertListEqual(new_ancestry, step.ancestry)

    def test_name_parent_nextstep_rename_conditional(self):
        step = Step(app='HelloWorld', action='helloWorld', ancestry=['step_parent'], name='step')
        nextstep = NextStep(name="test_nextstep", ancestry=step.ancestry)
        step.conditionals = [nextstep]

        new_ancestry = ["step_parent_update"]
        step.reconstruct_ancestry(new_ancestry)
        new_ancestry.append("step")
        new_ancestry.append("test_nextstep")
        self.assertListEqual(new_ancestry, step.conditionals[0].ancestry)

    def test_name_parent_nextstep_rename_error(self):
        step = Step(app='HelloWorld', action='helloWorld', ancestry=['step_parent'], name='step')
        next_step = NextStep(name="test_nextstep", ancestry=step.ancestry)
        step.errors = [next_step]

        new_ancestry = ["step_parent_update"]
        step.reconstruct_ancestry(new_ancestry)
        new_ancestry.append("step")
        new_ancestry.append("test_nextstep")
        self.assertListEqual(new_ancestry, step.errors[0].ancestry)

    def test_name_parent_multiple_nextstep_rename(self):
        step = Step(app='HelloWorld', action='helloWorld', ancestry=['step_parent'], name='step')
        next_step_one = NextStep(name="test_nextstep_one", ancestry=step.ancestry)
        next_step_two = NextStep(name="test_nextstep_two", ancestry=step.ancestry)
        step.conditionals = [next_step_one]
        step.errors = [next_step_two]

        new_ancestry = ["step_parent_update"]
        step.reconstruct_ancestry(new_ancestry)
        new_ancestry.append("step")
        new_ancestry.append("test_nextstep_one")
        self.assertListEqual(new_ancestry, step.conditionals[0].ancestry)

        new_ancestry.remove("test_nextstep_one")
        new_ancestry.append("test_nextstep_two")
        self.assertListEqual(new_ancestry, step.errors[0].ancestry)

    def test_set_input_valid(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        step.set_input({'num1': '-5.62', 'num2': '5', 'num3': '42.42'})
        self.assertDictEqual(step.input, {'num1': -5.62, 'num2': 5., 'num3': 42.42})

    def test_set_input_invalid_name(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'invalid': '5', 'num3': '42.42'})

    def test_set_input_invalid_format(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'num2': '5', 'num3': 'invalid'})