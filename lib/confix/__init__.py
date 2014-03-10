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

"""
    To define a record with a schema, create a subclass of Struct with a
    schema:

    class MyStruct(Struct):
        foo = FieldDef(type=int, doc='foo field', default=100)
        bar = FieldDef(type=str, doc='bar field')

    Fields may not begin with underscores, leading underscores are used by
    the Struct classes for internal data.

    There are three kinds of fields:
    Required fields: These must be defined by the user and have a value.  They
        are indicated by creating a FieldDef with a default of NoDefault.
    Defaulted Fields: These may be defined by the user, if not, they exist
        with a default value.  They are indicated by creating a FieldDef with
        a default of the default value.
    Optional Fields: These may be defined by the user, if not, they can be
        undefined.  Attempting to read them when they don't exist returns an
        attribute error, hasattr() can be used to query whether they exist.
        They can be indicated by creating a FieldDef with a default of
        Undefined.
"""

class NoDefault(object):
    """Used as a marker for the default value of fields with no default."""

class Undefined(object):
    """Used as a marker for the default value for fields that are undefined."""

class _StructMetaclass(type):

    def __new__(mcls, name, bases, dict):
        schema = {}
        for attr, val in dict.iteritems():
            if not attr.startswith('_'):

                # Make sure the value is a FieldDef.
                if not isinstance(val, FieldDef):
                    raise TypeError('Expected a FieldDef for the value of '
                                    'attribute %s' % attr)

                # If there is a default, make sure it's valid.
                if val.default not in (Undefined, NoDefault):
                    val.validate(val.default)

                val.name = attr
                schema[attr] = val

        # Remove the attributes from the class body.
        for attr in schema:
            del dict[attr]

        dict['_schema'] = schema
        return type.__new__(mcls, name, bases, dict)


def make_struct(name, schema):
    """Return a struct class with the given schema.

    Args:
        schema: {str: FieldDef} A schema dictionary mapping field names to
            field definitions.

    Returns:
        (class)
    """
    return _StructMetaclass(name, (Struct,), schema)


class FieldDef:
    """
        A field definition.

        Inst-vars:
            type: [any] argument type object.
            doc: [str] argument documentation.
            default: [any or NoDefault or Undefined] default value.  The special
                value of NoDefault indicates that there is no default value.
                The field must be provided by the creator of the structure.  The
                special value of Undefined indicates that there is no default
                value and that the creator of the structure doesn't need to
                define one.
            name: [str] the field name.
    """

    def __init__(self, type=None, doc=None, default=NoDefault, name=None):
        self.type = type
        self.doc = doc
        self.default = default
        self.name = name

    def validate(self, val):
        """
            Checks the argument value against its type.
        """
        if not isinstance(val, self.type):
            raise TypeError(val)


class Struct(object):
    """Strict records have an associated schema."""

    __metaclass__ = _StructMetaclass

    _strict = True
    _schema = {}
    _translation_data = {}

    def __init__(self, **kwargs):
        object.__init__(self)
        self.__dict__['_attrs'] = {}

        # Pre-fill with all optional attributes.  We don't do setattr here
        # because we don't need to type check.
        for attr, field_def in self._schema.iteritems():
            if field_def.default not in (Undefined, NoDefault):
                setattr(self, attr, field_def.default)

        for attr, val in kwargs.iteritems():
            setattr(self, attr, val)

    def __getattr__(self, attr):
        try:
            return self._attrs[attr]
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, attr, val):
        try:
            fieldDef = self._schema[attr]
            fieldDef.validate(val)
        except KeyError:
            if self._strict:
                raise AttributeError(attr)
        self._attrs[attr] = val

    def __cmp__(self, other):
        return cmp(self._attrs, other._attrs)

    def __dir__(self):
        return sorted(self._attrs.keys())


def set_translation_data(struct, key, value):
    """Sets arbitrary translation data on a Struct class.

    Translation data can be used by specific translator modules to store
    details of the mapping of a structure for the translation.

    Args:
        struct: type.  A Struct class.
        key: any object.  This is normally a class object known to the
            translation module.  The only constraint is that it be a globally
            unique key.
        value: any object.  The translation data.
    """
    struct._translation_data[key] = value


def get_translation_data(struct, key):
    """Returns translation data set by set_translation_data().

    Args:
        struct: type. A Struct class.
        key: any object.

    Raises:
        KeyError: Translation data for the key is not defined.
    """
    return struct._translation_data[key]


class LooseStruct(Struct):
    """A convenience class that lets you define a Struct with no schema."""

    _strict = False

    def __cmp__(self, other):
        return cmp(self._attrs, other._attrs)


def get_schema(struct):
    """Returns the schema for a struct instance.

    Args:
        struct: Struct instance.

    Returns:
        dict of str: FieldDef.
    """
    return struct._schema

def get_attrs(struct):
    """Returns the attributes of the structure as a dictionary.

    Args:
        struct: Struct instance.

    Returns:
        dict of str: object.
    """
    return struct._attrs
