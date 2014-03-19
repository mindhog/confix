# Copyright 2014 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import simplejson

import confix


def dict_to_struct(json_dict, struct_type=None):
    """Convert a dictionary representation of a JSON object to a Struct.

    Converts a dictionary representation of a JSON object of the form created
    by simplejson to a struct of the specified type.

    Args:
        json_dict: dict of str: object.
        struct_type: type derived from confix.Struct or None. The struct type
            to create an instance of.  If None, creates a confix.LooseStruct.

    Returns:
        confix.Struct or confix.LooseStruct.
    """
    if struct_type is None:
        struct_type = confix.LooseStruct
    result = struct_type()
    for key, val in json_dict.iteritems():
        setattr(result, key, intermediate_to_obj(val))
    return result


def string_to_struct(string_val, struct_type=None):
    """Convert a JSON string to a structure.

    Args:
        string_val: str.  A string containing a JSON object.
        struct_type: type derived from confix.Struct or None. The struct type
            to create an instance of.  If None, creates a confix.LooseStruct.

    Returns:
        confix.Struct or confix.LooseStruct.
    """
    dict_val = simplejson.loads(string_val)
    return dict_to_struct(dict_val, struct_type)


def intermediate_to_obj(intermediate, confix_type=None):
    """Converts from an intermediate representation to a confix object.

    Args:
        intermediate: A python object returned from a simplejson.load
            function.  These objects represent json objects as dicts, json
            lists as python lists, etc.
        confix_type: The type to convert to.

    Returns:
        A fix object corresponding to 'intermediate'.
    """
    if confix_type is None:
        if isinstance(intermediate, list):
            return [intermediate_to_obj(elem) for elem in intermediate]
        elif isinstance(intermediate, dict):
            return dict((key, intermediate_to_obj(val)) for key, val in
                        intermediate)
        else:
            return intermediate
    if issubclass(confix_type, confix.Generic):
        return confix_type.convert(intermediate, confix.convert_with_dicts)
    elif issubclass(confix_type, confix.Struct):
        return dict_to_struct(dict_val, struct_type)
    else:
        raise TypeError('%r is not a confix type (Generic or Struct)' %
                        confix_type)


def string_to_obj(string_val, confix_type=None):
    """Convert a JSON string to a confix object.

    Args:
        string_val: str.  A string containing a JSON object.
        confix_type: A confix type (Struct, List, Map).  If None, tries to
            create the right kind of thing based on the data.

    Returns:
        confix.Struct.
    """
    intermediate_val = simplejson.loads(string_val)
    return intermediate_to_obj(intermediate_val, confix_type)


def _encode(obj):
    if isinstance(obj, (confix.Struct)):
        json_dict = {}
        for attr, val in confix.get_attrs(obj).iteritems():
            if isinstance(val, confix.Struct):
                val = _encode(val)
            json_dict[attr] = val
        return json_dict
    else:
        raise TypeError('cannot convert %r to json' % obj)


def struct_to_string(struct):
    """Returns a JSON string representation of the struct.

    Args:
        struct: confix.Struct or confix.LooseStruct.

    Returns:
        str.
    """
    return simplejson.dumps(struct, default=_encode)

def read_struct(file, struct_type=None):
    """Returns a json struct read from the specified file.

    TODO(mmuller): Replace with read_obj()

    Args:
        file: file object or filename string.
        struct_type: type derived from confix.Struct or None. The struct type
            to create an instance of.  If None, creates a confix.LooseStruct.

    Returns:
        Struct.
    """
    if isinstance(file, basestring):
        file = open(file)
    return dict_to_struct(simplejson.load(file), struct_type)

def write_struct(file, struct):
    """Write the struct as JSON to the specified filename.

    TODO(mmuller): Replace with write_obj.

    Args:
        file: file object or filename string.
    """
    if isinstance(file, basestring):
        file = open(file, 'w')
    file.write(struct_to_string(struct))
