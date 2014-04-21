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

# pylint: disable=bad-indentation
# pylint: disable=redefined-builtin

import confix

# Avoid recursive local imports.
json = __import__('json')


def string_to_obj(string_val, confix_type=None):
    """Convert a JSON string to a confix object.

    Args:
        string_val: str.  A string containing a JSON object.
        confix_type: A confix type (Struct, List, Map).  If None, tries to
            create the right kind of thing based on the data.

    Returns:
        confix.Struct.
    """
    intermediate_val = json.loads(string_val)
    return confix.intermediate_to_obj(intermediate_val, confix_type)


def _encode(obj):
    if isinstance(obj, (confix.Struct)):
        json_dict = {}
        for attr, val in confix.get_attrs(obj).iteritems():
            if isinstance(val, confix.Struct):
                val = _encode(val)
            json_dict[attr] = val
        return json_dict
    elif isinstance(obj, confix.ListBase):
        return [_encode(item) for item in obj]
    elif isinstance(obj, confix.MapBase):
        return dict((str(_encode(key)), _encode(val))
                    for key, val in obj.iteritems())
    else:
        # This is not a confix type: just let the json encoder deal with it.
        return obj


def obj_to_string(obj):
    """Returns a JSON string representation of the struct.

    Args:
        obj: confix.Struct or confix.LooseStruct.

    Returns:
        str.
    """
    return json.dumps(obj, default=_encode)


def read_obj(file, confix_type=None):
    """Returns a confix object read from the specified file.

    Args:
        file: file object or filename string.
        confix_type: type derived from confix.Struct or confix.Generic or
            None. The struct type to create an instance of.  If None, infers
            the type from the data, creating a confix.LooseStruct for all
            dictionaries whose keys are legal attribute names.

    Returns:
        A confix object.
    """
    if isinstance(file, basestring):
        file = open(file)
    return confix.intermediate_to_obj(json.load(file), confix_type)


def write_obj(file, obj):
    """Write the confix object as JSON to the specified file.

    Args:
        file: file object or filename string.
        obj: Struct instance to write to the file.
    """
    if isinstance(file, basestring):
        file = open(file, 'w')
    file.write(obj_to_string(obj))
