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

import unittest

import protobuf


class ProtobufTests(unittest.TestCase):

    def testProto(self):
        loader = protobuf.ProtoLoader(roots=[''])
        MyMessage = loader.load('test.proto').MyMessage
        msg = MyMessage(a=100, b='data')
        self.assertEquals(msg.a, 100)
        self.assertEquals(msg.b, 'data')

        # Make sure that an unknown attribute raises an AttributeError.
        def SetBlech():
            msg.blech = 100
        self.assertRaises(AttributeError, SetBlech)

    def testMessgeCreation(self):
        loader = protobuf.ProtoLoader(roots=[''])
        MyMessage = loader.load('test.proto').MyMessage
        struct = MyMessage(a=100, b='data')
        msg = protobuf.struct_to_message(struct)
        self.assertEquals(msg.a, 100)
        self.assertEquals(msg.b, 'data')
        self.assertFalse(msg.HasField('x'))

        # Serialize the message to a string and try to resurrect it as a
        # struct.
        bin_string = msg.SerializeToString()
        resurrected = protobuf.string_to_struct(bin_string, MyMessage)
        self.assertEquals(resurrected, struct)


if __name__ == '__main__':
    unittest.main()
