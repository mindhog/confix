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

import os
import unittest

from confix import protobuf

TEST_PROTO = 'test.proto'
PROTO_ROOT = ''


class ProtobufTests(unittest.TestCase):

    def testProto(self):
        loader = protobuf.ProtoLoader(roots=[PROTO_ROOT])
        MyMessage = loader.load(TEST_PROTO).MyMessage
        msg = MyMessage(a=100, b='data')
        self.assertEqual(msg.a, 100)
        self.assertEqual(msg.b, 'data')

        # Make sure that an unknown attribute raises an AttributeError.
        def SetBlech():
            msg.blech = 100
        self.assertRaises(AttributeError, SetBlech)

    def testMessageCreation(self):
        loader = protobuf.ProtoLoader(roots=[PROTO_ROOT])
        MyMessage = loader.load(TEST_PROTO).MyMessage
        struct = MyMessage(a=100, b='data')
        msg = protobuf.obj_to_message(struct)
        self.assertEqual(msg.a, 100)
        self.assertEqual(msg.b, 'data')
        self.assertFalse(msg.HasField('x'))

        # Serialize the message to a string and try to resurrect it as a
        # struct.
        bin_string = msg.SerializeToString()
        resurrected = protobuf.string_to_obj(bin_string, MyMessage)
        self.assertEqual(resurrected, struct)

    def testFileNotFound(self):
        loader = protobuf.ProtoLoader(roots=[PROTO_ROOT])
        self.assertRaises(protobuf.ProtoFileNotFound, loader.load,
                          'bogus.proto')

    def testGlobalLoader(self):
        protobuf.clear_loader()
        protobuf.add_root(PROTO_ROOT)
        MyMessage = protobuf.load(TEST_PROTO).MyMessage
        self.assertEqual(MyMessage(a=100, b='data').a, 100)

        self.assertRaises(protobuf.LoaderAlreadyDefined,
                          protobuf.add_root, 'foo')


if __name__ == '__main__':
    unittest.main()
