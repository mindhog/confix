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

"""Confix YAML translator."""

from StringIO import StringIO

import confix

# Use the low-level __import__ function to implement the global yaml module.
# ('import yaml' would recursively import this module.)
yaml = __import__('yaml')


def read_obj(file, confix_type=None):
    """Read an object from the file.

    Args:
        file: (file) File object to read from.
        confix_type: (confix type or None) This is the type of the top-level
            object.  If None, does a best effort translation, converting
            top-level dictionaries to LooseStruct, and converting most nested
            types to their corresponding python types.
            TODO(mmuller): Improve best-effort, convert nested dicts to
            LooseStructs when appropriate.

    Returns:
        A confix object.
    """
    return confix.intermediate_to_obj(yaml.safe_load(file), confix_type)


def string_to_obj(yaml_string, confix_type=None):
    """Read an object from a string.

    Args:
        yaml_string: (str) String containing a yaml object representation.
        confix_type: (confix type or None) This is the type of the top-level
            object.  If None, does a best effort translation, converting
            top-level dictionaries to LooseStruct, and converting most nested
            types to their corresponding python types.
            TODO(mmuller): Improve best-effort, convert nested dicts to
            LooseStructs when appropriate.

    Returns:
        A confix object.
    """
    return read_obj(StringIO(yaml_string), confix_type)


# It wasn't obvious after a short amount of examination how to get PyYaml to
# treat objects with attributes as dictionaries or how to convert nodes on an
# individual basis, so we just convert the entire object tree to plain
# dictionaries, lists and leafs.
def _to_intermediate(obj):
    if isinstance(obj, confix.MapBase):
        inter = {}
        for key, val in obj.iteritems():
            inter[_to_intermediate(key)] = _to_intermediate(val)
    elif isinstance(obj, confix.ListBase):
        inter = []
        for item in obj:
            inter.append(_to_intermediate(item))
    elif isinstance(obj, confix.Struct):
        inter = {}
        for attr, val in confix.get_attrs(obj).iteritems():
            inter[attr] = _to_intermediate(val)
    else:
        inter = obj
    return inter


def write_obj(file, obj, default_flow_style=True):
    """Writes 'obj' as a json file.

    Args:
        file: (file) The file object to write to.
        obj: (confix object) Te object to write.
        default_flow_style: (bool) If true, nested yaml objects are written in
            "flow" format (with lists and dicts on a single line) when the
            underlying code deems appropriate.
    """
    yaml.dump(_to_intermediate(obj), file,
              default_flow_style=default_flow_style)


def obj_to_string(obj, default_flow_style=True):
    """Returns 'obj' as a json string.

    Args:
        obj: (confix object) Te object to write.
        default_flow_style: (bool) If true, nested yaml objects are written in
            "flow" format (with lists and dicts on a single line) when the
            underlying code deems appropriate.
    """
    dst = StringIO()
    write_obj(dst, obj, default_flow_style=default_flow_style)
    return dst.getvalue()
