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

import StringIO
import unittest
import confix
from confix import json

class TestStruct(confix.Struct):
    a = confix.FieldDef(int, 'a variable')
    b = confix.FieldDef(str, 'other variable')

class JsonTest(unittest.TestCase):

    def testFromJSON(self):
        obj = json.string_to_struct('{"a": 100, "b": "some value"}')
        self.assertEquals(obj, confix.LooseStruct(a=100, b='some value'))

        obj = json.string_to_struct('{"a": 100, "b": "some value"}',
                                    TestStruct)
        self.assertEquals(obj, TestStruct(a=100, b='some value'))

    def testToJson(self):
        obj = TestStruct(a=100, b='test val')
        self.assertEquals(json.struct_to_string(obj),
                          '{"a": 100, "b": "test val"}')

    def testReadWrite(self):
        obj = json.read_struct(StringIO.StringIO('{"a": 100, "b": "test val"}'),
                               TestStruct)
        self.assertEquals(obj, TestStruct(a=100, b='test val'))
        out = StringIO.StringIO()
        json.write_struct(out, obj)
        self.assertEquals(out.getvalue(), '{"a": 100, "b": "test val"}')

        # Try it with a real file.
        obj = TestStruct(a=100, b='test val')
        json.write_struct('testfile.json', obj)
        obj2 = json.read_struct('testfile.json', TestStruct)
        self.assertEquals(obj, obj2)

if __name__ == '__main__':
    unittest.main()
