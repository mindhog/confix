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

    # --- getting schemas from protobufs ---

    from confix import protobuf

    pl = protobuf.ProtoLoader(roots=[''])
    MyMessage = pl.load('mymessage.proto').MyMessage

    msg = MyMessage(a=100, b='value')
    protobuf.write_to_file('filename.pb', msg)

    # --- translating from json ---

    from confix import json

    msg = json.read_file('filename.json', MyMessage)
    protobuf.write_to_file('filename.pb', msg)

"""

from google.protobuf import descriptor
from google.protobuf import descriptor_pb2
from google.protobuf import message
from google.protobuf import reflection
from protoc import Importer, DiskSourceTree, StdErrErrorCollector, \
    ToBinary
import confix


class MessageDef(object):
    """A protobuf message definition.

    This stores information about a message to be stored with a struct class.
    This is initialized with a descriptor_pb, the other attributes are created
    on demand.

    Attributes:
        descriptor_pb: descriptor_pb2.DescriptorProto.
        descriptor: descriptor.Descriptor.
        type: Type derived from message.Message.  Can be used to construct
            actual message object instances.
    """
    def __init__(self, descriptor_pb):
        self.descriptor_pb = descriptor_pb
        self.__descriptor = None
        self.__type = None

    @property
    def descriptor(self):
        if self.__descriptor is None:
            self.__descriptor = descriptor.MakeDescriptor(self.descriptor_pb)
        return self.__descriptor

    @property
    def type(self):
        if self.__type is None:
            self.__type = reflection.GeneratedProtocolMessageType(
                str(self.descriptor_pb.name),
                (message.Message,),
                {'DESCRIPTOR': self.descriptor})
        return self.__type


def convert_to_struct(message):
    """Returns a confix.Struct class for the message.

    Args:
        message: descriptor_pb2.DescriptorProto
    """
    schema = {}
    for field in message.field:

        # TODO(mmuller): finish implementing this.
        fdp = descriptor_pb2.FieldDescriptorProto
        if field.type == fdp.TYPE_INT32:
            type = int
        elif field.type in (fdp.TYPE_FLOAT, fdp.TYPE_DOUBLE):
            type = float
        elif field.type == fdp.TYPE_STRING:
            type = basestring
        else:
            raise NotImplementedError("Use of type %d which hasn't been "
                                      "implemented yet")

        default_val = (field.default_value if field.HasField('default_value') else
                       confix.NoDefault)

        field_def = confix.FieldDef(name=field.name, type=type, default=default_val)
        schema[field.name] = field_def

    struct = confix.make_struct(str(message.name), schema)
    confix.set_translation_data(struct, MessageDef, MessageDef(message))
    return struct


class ProtoDefFile(object):
    """A protobuf definiton file object.

    Instances should contain an attribute for every message in a proto
    descriptor file.
    """


class Error(Exception):
    """Error base class for protobufs."""


class ProtoFileNotFound(Error):
    """Raised by ProtoLoader.load() when the protofile is not found."""


class LoaderAlreadyDefined(Error):
    """Raised by add_root() when the loader is already defined."""


class ProtoLoader(object):

    def __init__(self, roots=None):
        """
        Args:
            roots: list of root directories or None.  The root directories to
                load .proto files from, both user specified and imported ones.
        """
        self.__source_tree = DiskSourceTree()
        if roots:
            for root in roots:
                self.__source_tree.MapPath('', root)
        self.__error_collector = StdErrErrorCollector()
        self.__importer = Importer(self.__source_tree, self.__error_collector)

    def load(self, path):
        """Loads a protodefinition file and returns a proxy object for it.

        Args:
            path: (str) .proto file path name.

        Returns:
            An object with a field for every message defined in the protofile,
            where the fields are assigned to confix.Struct classes whose schema
            reflects that of the message.

        Raises:
            ProtoFileNotFound: The file wasn't found.
        """

        # Load the file descriptor and convert it to a protobuf.
        file_des = self.__importer.Import(path)
        if not file_des:
            raise ProtoFileNotFound()
        file_des_pb = descriptor_pb2.FileDescriptorProto()
        file_des_pb.MergeFromString(ToBinary(file_des))

        result = ProtoDefFile()

        # Now convert all messages in the file descriptor to schemas.
        for message in file_des_pb.message_type:
            message_struct = convert_to_struct(message)
            setattr(result, message.name, message_struct)

        return result


def struct_to_message(struct):
    """Returns a message object for the structure.

    Args:
        struct: confix.Struct.

    Returns:
        google.protobuf.message.Message.
    """
    msg_def = confix.get_translation_data(struct, MessageDef)
    msg = msg_def.type()
    fdp = descriptor_pb2.FieldDescriptorProto

    for field in msg_def.descriptor_pb.field:
        try:
            val = getattr(struct, field.name)

            # Don't set optional fields that are the default value.
            if (field.label != fdp.LABEL_OPTIONAL or
                val != field.default_value):
                setattr(msg, field.name, val)
        except AttributeError:
            # Make sure it's optional.
            if field.label != fdp.LABEL_OPTIONAL:
                raise AttributeError('Required field %s is undefined' %
                                     field.name)

    return msg


def message_to_struct(msg, struct_type):
    """Converts a protobuf message to a Struct.

    Args:
        msg: message.Message
        struct_type: type derived from Struct.  The struct type to extract.
    """
    result = struct_type()
    for name, field_def in confix.get_schema(struct_type).iteritems():
        if msg.HasField(name):
            setattr(result, name, getattr(msg, name))
    return result


def string_to_struct(string, struct_type):
    """Returns an instance of 'struct_type' parsed from 'string'.

    Args:
        string: str.  A string containing a serialized protobuf of type
            corresponding to 'struct'.
        struct_type: type derived from confix.Struct.  The structure type that
            we are returning an instance of.

    Returns:
        Instance of struct_type.

    Raises:
        KeyError: The struct_type has never been bound to a message type.
    """
    msg_def = confix.get_translation_data(struct_type, MessageDef)
    msg = msg_def.type()
    msg.MergeFromString(string)

    return message_to_struct(msg, struct_type)


# The global loader and its root directories.
_loader = None
_roots = []


def load(proto_file):
    """Loads the specified proto_file.

    This is equivalent to ProtoLoader.load() except that it uses a global
    ProtoLoader, which is probably suitable for most applications.

    Args:
        proto_file: str
    """
    global _loader, _roots
    if not _loader:
        _loader = ProtoLoader(_roots)
    return _loader.load(proto_file)


def clear_loader():
    """Clears the global loader used by load().

    This is primarily intended for testing purposes.
    """
    _loader = None


def add_root(path):
    """Adds a root path to the list of paths for the global loader.

    See load().  Root paths used as root directories when searching for proto
    files.

    Args:
        path: str.  A root path.

    Raises:
        LoaderAlreadyDefined: Root paths cannot be added because the loader
        has already been created.
    """
    if _loader:
        raise LoaderAlreadyDefined()
    _roots.append(path)
