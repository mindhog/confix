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

import re


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
                    val.default = val.convert(val.default)

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


def _convert(type, val, convert_func=None):
    """Convert 'val' to an instance of 'type'.

    Args:
        type: type object.
        val: object.
        convert_func: callable(type, val).  If specified, this is the function
            to use to convert nested values.

    Returns:
        Instance of type.

    Raises:
        TypeError: The value was not convertible.
    """
    if isinstance(val, type):
        return val
    elif issubclass(type, Generic):
        return type.convert(val, convert_func or _convert)
    else:
        raise TypeError(val)


def convert_with_dicts(type, val):
    """Convert 'val' to an instance of 'type'.

    This is different from _convert in that it accepts dicts when converting
    to a Struct.
    """
    try:
        return _convert(type, val, convert_with_dicts)
    except TypeError:
        if issubclass(type, Struct) and isinstance(val, dict):
            obj = type()
            for key, val in val.iteritems():
                setattr(obj, key, val)
            return obj
        else:
            raise


def dict_to_struct(json_dict, struct_type=None, convert_func=None):
    """Convert a dictionary representation of a JSON object to a Struct.

    Converts a dictionary representation of a JSON object of the form created
    by simplejson to a struct of the specified type.

    Args:
        json_dict: dict of str: object.
        struct_type: type derived from confix.Struct or None. The struct type
            to create an instance of.  If None, creates a LooseStruct.
        convert_func: callable(type, value).  If specified, this is a
                function to convert nested objects.

    Returns:
        Struct or LooseStruct.
    """
    if struct_type is None:
        struct_type = LooseStruct
    result = struct_type()
    for key, val in json_dict.iteritems():
        setattr_with_convert_func(result, key, val, convert_func or _convert)
    return result


# Regular expression to match a legal attribute name.
ATTR_NAME_RX = re.compile(r'[a-zA-Z]\w*$')


def intermediate_to_obj(intermediate, confix_type=None, convert_func=None):
    """Converts from an intermediate representation to a confix object.

    Args:
        intermediate: A python object of the kind returned by the simplejson
            and pyyaml load functions.  These objects represent structs as
            dicts.
        confix_type: The type to convert to.
        convert_func: callable(type, value).  If specified, this is a
                function to convert nested objects.

    Returns:
        A fix object corresponding to 'intermediate'.
    """
    if confix_type is None:
        if isinstance(intermediate, list):
            return [intermediate_to_obj(elem) for elem in intermediate]
        elif isinstance(intermediate, dict):

            # See if all of the keys are attribute names.
            for key in intermediate:
                if not ATTR_NAME_RX.match(key):
                    # Nope.  Create a dict.
                    return dict((key, intermediate_to_obj(val)) for key, val in
                                intermediate.iteritems())
                else:
                    return dict_to_struct(intermediate)
        else:
            return intermediate
    if issubclass(confix_type, Generic):
        return confix_type.convert(intermediate, convert_with_dicts)
    elif issubclass(confix_type, Struct):
        return dict_to_struct(intermediate, confix_type,
                              convert_func or
                              (lambda t, v: intermediate_to_obj(v, t)))
    else:
        return _convert(confix_type, intermediate)


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

    def convert(self, val):
        """Converts the value to the field type."""
        return _convert(self.type, val)

    def __str__(self):
        return ('FieldDef(type=%r, doc=%r, default=%r, name=%r)' %
                (self.type, self.doc, self.default, self.name))


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
                try:
                    setattr(self, attr, field_def.default)
                except TypeError, ex:
                    raise TypeError('%r (default for attribute %s)' %
                                    (ex[0], attr))

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
            val = fieldDef.convert(val)
        except KeyError:
            if self._strict:
                raise AttributeError(attr)
        self._attrs[attr] = val

    def __cmp__(self, other):
        if isinstance(other, Struct):
            return cmp(self._attrs, other._attrs)
        else:
            return id(self) - id(other)

    def __dir__(self):
        return sorted(self._attrs.keys())


class Generic(object):
    """Base class for generics.

    As in other languages, generics are types parameterized by other types.
    They are used in confix to implement containers.

    This base class only exists so we can check that a value is an instance of
    it during conversion and as a place to document the interface.
    """

    @classmethod
    def convert(cls, value, convert_func=_convert):
        """Converts 'value' to the generic type.

        Converts or raises a TypeError if the value cannot be converter.  If
        'value' is already of the appropriate type, this simply returns 'value'.

        Must be implemented by derived class.

        Args:
            value: object
            convert_func: callable(type, value).  If specified, this is a
                function to convert nested objects.
        """
        raise NotImplementedError()


class ListBase(Generic):
    """Base class for List<T>."""

    def __init__(self, elems):
        self._elems = list(elems)

    def __setitem__(self, index, val):
        self._elems[index] = _convert(self._elem_type, val)

    def __getitem__(self, index):
        return self._elems[index]

    def __iter__(self):
        return iter(self._elems)

    def __str__(self):
        return '%s(%r)' % (self.__class__.__name__, self._elems)

    __repr__ = __str__

    def append(self, val):
        self._elems.append(_convert(self._elem_type, val))

    def __cmp__(self, other):
        return cmp(self._elems, other)

    @classmethod
    def convert(cls, value, convert_func=_convert):
        if isinstance(value, cls):
            return value
        elif isinstance(value, list):
            return cls(convert_func(cls._elem_type, item) for item in value)
        else:
            raise TypeError(value)


# Cache to keep track of the generic types that we'va already created.  Keys
# are tuples of the generic base class (e.g. 'ListBase') followed by its
# parameter types.  A list of strings would have the key (ListBase, str) .
# Values are the constructed types themselves.
_generic_cache = {}


def List(elem_type):
    """Returns a list class with the specified element type."""
    global _generic_cache
    try:
        return _generic_cache[(ListBase, elem_type)]
    except KeyError:
        _generic_cache[(ListBase, elem_type)] = t = (
            type('ListOf<%s>' % elem_type.__name__, (ListBase,),
                 {'_elem_type': elem_type}))
        return t


class MapBase(Generic):
    """Base class for Map<T>."""

    def __init__(self, normal_map, convert_func=_convert):
        self._map = {}
        for key, val in normal_map.iteritems():
            self._map[convert_func(self._key_type, key)] = (
                convert_func(self._val_type, val))

    @classmethod
    def convert(cls, val, convert_func=_convert):
        # Verify that we have iteritems.
        try:
            val.iteritems
        except AttributeError:
            raise TypeError(val)
        return cls(val, convert_func=convert_func)

    def __getitem__(self, key):
        return self._map[key]

    def __setitem__(self, key, val):
        self._map[_convert(self._key_type, key)] = (
            _convert(self._val_type, val))

    def __cmp__(self, other):
        return cmp(self._map, other)

    def get(self, key, default=None):
        try:
            return self._map[_convert(self._key_type, key)]
        except KeyError:
            return None if default is None else _convert(self._val_type, default)

    def setdefault(self, key, default):
        try:
            return self._map[_convert(self._key_type, key)]
        except KeyError:
            val = _convert(self._val_type, default)
            self._map[_convert(self._key_type, key)] = val
            return val

    def keys(self):
        return self._map.keys()

    def values(self):
        return self._map.values()

    def items(self):
        return self._map.items()

    def iterkeys(self):
        return self._map.iterkeys()

    def itervalues(self):
        return self._map.itervalues()

    def iteritems(self):
        return self._map.iteritems()


def Map(key_type, val_type):
    """Returns a Map class with the specified key and value types."""
    global _generic_cache
    try:
        return _generic_cache[MapBase, key_type, val_type]
    except KeyError:
        _generic_cache[MapBase, key_type, val_type] = t = (
            type('Map<%s, %s>' % (key_type.__name__, val_type.__name__),
                 (MapBase,),
                 {'_key_type': key_type, '_val_type': val_type}))
        return t


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


def setattr_with_convert_func(struct, attr, val, convert_func):
    """Sets the attribute with the specified conversion function."""
    # This is duplicated in Struct.__setattr__() because __setattr__ is used a
    # lot and we don't want to make it too abstract.
    try:
        fieldDef = struct._schema[attr]
        val = convert_func(fieldDef.type, val)
    except KeyError:
        if struct._strict:
            raise AttributeError(attr)
    struct._attrs[attr] = val
