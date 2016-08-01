# Copyright (c) 2015 Tanium Inc
#

import csv
import io
import json
import re
try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET


class IncorrectTypeException(Exception):
    """Raised when a property is not of the expected type"""
    def __init__(self, property, expected, actual):
        self.property = property
        self.expected = expected
        self.actual = actual
        err = 'Property {} is not of type {}, got {}'.format
        Exception.__init__(self, err(property, str(expected), str(actual)))


class BaseType(object):

    _soap_tag = None

    def __init__(self, simple_properties, complex_properties,
                 list_properties):
        self._initialized = False
        self._simple_properties = simple_properties
        self._complex_properties = complex_properties
        self._list_properties = list_properties
        self._initialized = True

    def __getitem__(self, n):
        """Allow automatic indexing into lists.

        Only supported on types that have a single property
        that is in list_properties

        """
        if len(self._list_properties) == 1:
            return getattr(self, self._list_properties.items()[0][0])[n]
        else:
            raise Exception(
                'Not simply a list type, __getitem__ not supported'
            )

    def __len__(self):
        """Allow len() for lists.

        Only supported on types that have a single property
        that is in list_properties

        """
        if len(self._list_properties) == 1:
            return len(getattr(self, self._list_properties.items()[0][0]))
        else:
            raise Exception('Not simply a list type, len() not supported')

    def __str__(self):
        class_name = self.__class__.__name__
        val = ''
        if len(self._list_properties) == 1:
            val = ', len: {}'.format(len(self))
        else:
            if getattr(self, 'name', ''):
                val += ', name: {!r}'.format(self.name)
            if getattr(self, 'id', ''):
                val += ', id: {!r}'.format(self.id)
            if not val:
                vals = [
                    '{}: {!r}'.format(p, getattr(self, p, ''))
                    for p in sorted(self._simple_properties)
                ]
                if vals:
                    vals = "\t" + "\n\t".join(vals)
                    val = ', vals:\n{}'.format(vals)
        ret = '{}{}'.format(class_name, val)
        return ret

    def __setattr__(self, name, value):
        """Enforce type, if name is a complex property"""
        if value is not None and \
                name != '_initialized' and \
                self._initialized and \
                name in self._complex_properties:
            if not isinstance(value, self._complex_properties[name]):
                raise IncorrectTypeException(
                    value,
                    self._complex_properties[name],
                    type(value)
                )
        super(BaseType, self).__setattr__(name, value)

    def append(self, n):
        """Allow adding to list.

        Only supported on types that have a single property
        that is in list_properties

        """
        if len(self._list_properties) == 1:
            getattr(self, self._list_properties.items()[0][0]).append(n)
        else:
            raise Exception(
                'Not simply a list type, append not supported'
            )

    def toSOAPElement(self, minimal=False): # noqa
        root = ET.Element(self._soap_tag)
        for p in self._simple_properties:
            el = ET.Element(p)
            val = getattr(self, p)
            if val is not None:
                el.text = str(val)
            if val is not None or not minimal:
                root.append(el)
        for p, t in self._complex_properties.iteritems():
            val = getattr(self, p)
            if val is not None or not minimal:
                if val is not None and not isinstance(val, t):
                    raise IncorrectTypeException(p, t, type(val))
                if isinstance(val, BaseType):
                    child = val.toSOAPElement(minimal=minimal)
                    # the tag name is the property name,
                    # not the property type's soap tag
                    el = ET.Element(p)
                    if child.getchildren() is not None:
                        for child_prop in child.getchildren():
                            el.append(child_prop)
                    root.append(el)
                else:
                    el = ET.Element(p)
                    root.append(el)
                    if val is not None:
                        el.append(str(val))
        for p, t in self._list_properties.iteritems():
            vals = getattr(self, p)
            if not vals:
                continue
            # fix for str types in list props
            if issubclass(t, BaseType):
                for val in vals:
                    root.append(val.toSOAPElement(minimal=minimal))
            else:
                for val in vals:
                    el = ET.Element(p)
                    root.append(el)
                    if val is not None:
                        el.text = str(val)
                    if vals is not None or not minimal:
                        root.append(el)
        return root

    def toSOAPBody(self, minimal=False): # noqa
        out = io.BytesIO()
        ET.ElementTree(self.toSOAPElement(minimal=minimal)).write(out)
        return out.getvalue()

    @classmethod
    def fromSOAPElement(cls, el): # noqa
        result = cls()
        for p, t in result._simple_properties.iteritems():
            pel = el.find("./{}".format(p))
            if pel is not None and pel.text:
                setattr(result, p, t(pel.text))
            else:
                setattr(result, p, None)
        for p, t in result._complex_properties.iteritems():
            elems = el.findall('./{}'.format(p))
            if len(elems) > 1:
                raise Exception(
                    'Unexpected: {} elements for property'.format(p)
                )
            elif len(elems) == 1:
                setattr(
                    result,
                    p,
                    result._complex_properties[p].fromSOAPElement(elems[0]),
                )
            else:
                setattr(result, p, None)
        for p, t in result._list_properties.iteritems():
            setattr(result, p, [])
            elems = el.findall('./{}'.format(p))
            for elem in elems:
                if issubclass(t, BaseType):
                    getattr(result, p).append(t.fromSOAPElement(elem))
                else:
                    getattr(result, p).append(elem.text)

        return result

    @classmethod
    def fromSOAPBody(cls, body): # noqa
        """Parse body (text) and produce Python tanium objects.

        This method assumes a single result_object, which
        may be a list or a single object.

        """
        tree = ET.fromstring(body)
        result_object = tree.find(".//result_object/*")
        if result_object is None:
            return None  # no results, not an error
        # based on the tag of the matching element,
        # find the appropriate tanium_type and deserialize
        from object_list_types import OBJECT_LIST_TYPES
        if result_object.tag not in OBJECT_LIST_TYPES:
            raise Exception('Unknown type {}'.format(result_object.tag))
        r = OBJECT_LIST_TYPES[result_object.tag].fromSOAPElement(result_object)
        r._RESULT_OBJECT = result_object
        return r

    def flatten_jsonable(self, val, prefix):
        result = {}
        if type(val) == list:
            for i, v in enumerate(val):
                result.update(self.flatten_jsonable(
                    v,
                    '_'.join([prefix, str(i)]))
                )
        elif type(val) == dict:
            for k, v in val.iteritems():
                result.update(self.flatten_jsonable(
                    v,
                    '_'.join([prefix, k] if prefix else k))
                )
        else:
            result[prefix] = val
        return result

    def to_flat_dict_explode_json(self, val, prefix=""):
        """see if the value is json. If so, flatten it out into a dict"""
        try:
            js = json.loads(val)
            return self.flatten_jsonable(js, prefix)
        except Exception:
            return None

    def to_flat_dict(self, prefix='', explode_json_string_values=False):
        """Convert the object to a dict, flattening any lists or nested types
        """
        result = {}
        prop_start = '{}_'.format(prefix) if prefix else ''
        for p, _ in self._simple_properties.iteritems():
            val = getattr(self, p)
            if val is not None:
                json_out = None
                if explode_json_string_values:
                    json_out = self.to_flat_dict_explode_json(val, p)
                if json_out is not None:
                    result.update(json_out)
                else:
                    result['{}{}'.format(prop_start, p)] = val
        for p, _ in self._complex_properties.iteritems():
            val = getattr(self, p)
            if val is not None:
                result.update(val.to_flat_dict(
                    prefix='{}{}'.format(prop_start, p),
                    explode_json_string_values=explode_json_string_values,
                ))
        for p, _ in self._list_properties.iteritems():
            val = getattr(self, p)
            if val is not None:
                for ind, item in enumerate(val):
                    prefix = '{}{}_{}'.format(prop_start, p, ind)
                    if isinstance(item, BaseType):
                        result.update(item.to_flat_dict(
                            prefix=prefix,
                            explode_json_string_values=explode_json_string_values,
                        ))
                    else:
                        result[prefix] = item
        return result

    def explode_json(self, val):
        try:
            return json.loads(val)
        except Exception:
            return None

    def to_jsonable(self, explode_json_string_values=False, include_type=True):
        result = {}
        if include_type:
            result['_type'] = self._soap_tag
        for p, _ in self._simple_properties.iteritems():
            val = getattr(self, p)
            if val is not None:
                json_out = None
                if explode_json_string_values:
                    json_out = self.explode_json(val)
                if json_out is not None:
                    result[p] = json_out
                else:
                    result[p] = val
        for p, _ in self._complex_properties.iteritems():
            val = getattr(self, p)
            if val is not None:
                result[p] = val.to_jsonable(
                    explode_json_string_values=explode_json_string_values,
                    include_type=include_type)
        for p, _ in self._list_properties.iteritems():
            val = getattr(self, p)
            if val is not None:
                result[p] = []
                for ind, item in enumerate(val):
                    if isinstance(item, BaseType):
                        result[p].append(item.to_jsonable(
                            explode_json_string_values=explode_json_string_values,
                            include_type=include_type))
                    else:
                        result[p].append(item)
        return result

    @staticmethod
    def to_json(jsonable, **kwargs):
        """Convert to a json string.

        jsonable can be a single BaseType instance of a list
        of BaseType

        """
        if type(jsonable) == list:
            return json.dumps(
                [item.to_jsonable(**kwargs) for item in jsonable],
                sort_keys=True,
                indent=2,
            )
        else:
            return json.dumps(
                jsonable.to_jsonable(**kwargs),
                sort_keys=True,
                indent=2,
            )

    @classmethod
    def _from_json(cls, jsonable):
        """Private helper to parse from JSON after type is instantiated"""
        result = cls()
        for p, t in result._simple_properties.iteritems():
            val = jsonable.get(p)
            if val is not None:
                setattr(result, p, t(val))
        for p, t in result._complex_properties.iteritems():
            val = jsonable.get(p)
            if val is not None:
                setattr(result, p, BaseType.from_jsonable(val))
        for p, t in result._list_properties.iteritems():
            val = jsonable.get(p)
            if val is not None:
                vals = []
                for item in val:
                    if issubclass(t, BaseType):
                        vals.append(BaseType.from_jsonable(item))
                    else:
                        vals.append(item)
                setattr(result, p, vals)
        return result

    @staticmethod
    def from_jsonable(jsonable):
        """Inverse of to_jsonable, with explode_json_string_values=False.

        This can be used to import objects from serialized JSON. This JSON should come from BaseType.to_jsonable(explode_json_string_values=False, include+type=True)

        Examples
        --------
        >>> with open('question_list.json') as fd:
        ...    questions = json.loads(fd.read())
        ...    # is a list of serialized questions
        ...    question_objects = BaseType.from_jsonable(questions)
        ...    # will return a list of api.Question

        """
        if type(jsonable) == list:
            return [BaseType.from_jsonable(item for item in list)]
        elif type(jsonable) == dict:
            if not jsonable.get('_type'):
                raise Exception('JSON must contain _type to be deserialized')
            from object_list_types import OBJECT_LIST_TYPES
            if jsonable['_type'] not in OBJECT_LIST_TYPES:
                raise Exception('Unknown type {}'.format(jsonable['_type']))
            result = OBJECT_LIST_TYPES[jsonable['_type']]._from_json(jsonable)
            return result
        else:
            raise Exception('Expected list or dict to deserialize')

    @staticmethod
    def write_csv(fd, val, explode_json_string_values=False, **kwargs):
        """Write 'val' to CSV. val can be a BaseType instance or a list of
        BaseType

        This does a two-pass, calling to_flat_dict for each object, then
        finding the union of all headers,
        then writing out the value of each column for each object
        sorted by header name

        explode_json_string_values attempts to see if any of the str values
        are parseable by json.loads, and if so treat each property as a column
        value

        fd is a file-like object
        """
        def sort_headers(headers, **kwargs):
            '''returns a list of sorted headers (Column names)
            If kwargs has 'header_sort':
              if header_sort == False, do no sorting
              if header_sort == [] or True, do sorted(headers)
              if header_sort == ['col1', 'col2'], do sorted(headers), then
                put those headers first in order if they exist
            '''
            header_sort = kwargs.get('header_sort', [])

            if header_sort is False:
                return headers
            elif header_sort is True:
                pass
            elif not type(header_sort) in [list, tuple]:
                raise Exception("header_sort must be a list!")

            headers = sorted(headers)

            if header_sort is True or not header_sort:
                return headers

            custom_sorted_headers = []
            for hs in header_sort:
                for hidx, h in enumerate(headers):
                    if h.lower() == hs.lower():
                        custom_sorted_headers.append(headers.pop(hidx))

            # append the rest of the sorted_headers that didn't
            # match header_sort
            custom_sorted_headers += headers
            return custom_sorted_headers

        def fix_newlines(val):
            if type(val) == str:
                # turn \n into \r\n
                val = re.sub(r"([^\r])\n", r"\1\r\n", val)
            return val

        base_type_list = [val] if isinstance(val, BaseType) else val
        headers = set()
        for base_type in base_type_list:
            row = base_type.to_flat_dict(explode_json_string_values=explode_json_string_values)
            for col in row:
                headers.add(col)

        writer = csv.writer(fd)

        headers_sorted = sort_headers(list(headers), **kwargs)
        writer.writerow(headers_sorted)

        for base_type in base_type_list:
            row = base_type.to_flat_dict(explode_json_string_values=explode_json_string_values)
            writer.writerow(
                [fix_newlines(row.get(col, '')) for col in headers_sorted]
            )
