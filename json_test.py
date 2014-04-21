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

import os
import StringIO
import unittest

import confix
from confix import json


class TestStruct(confix.Struct):
    a = confix.FieldDef(int, 'a variable')
    b = confix.FieldDef(basestring, 'other variable')


class SimpleJsonTest(unittest.TestCase):

    def testFromJSON(self):
        obj = json.string_to_obj('{"a": 100, "b": "some value"}')
        self.assertEqual(obj, confix.LooseStruct(a=100, b='some value'))

        obj = json.string_to_obj('{"a": 100, "b": "some value"}',
                                 TestStruct)
        self.assertEqual(obj, TestStruct(a=100, b='some value'))

        obj = json.string_to_obj('[1, 2, 3]', confix.List(int))
        self.assertEqual(obj, [1, 2, 3])

        obj = json.string_to_obj('{"foo": 100, "bar": 200}',
                                 confix.Map(basestring, int))
        self.assertEqual(obj, {'foo': 100, 'bar': 200})

        obj = json.string_to_obj('{"foo": {"a": 100, "b": "string val"}}',
                                 confix.Map(basestring, TestStruct))
        self.assertEqual(obj, {'foo': TestStruct(a=100, b='string val')})

        obj = json.string_to_obj(('[{"a": 1, "b": "two"}, '
                                  '{"a": 3, "b": "four"}]'),
                                 confix.List(TestStruct))
        self.assertEqual(obj,
                         [TestStruct(a=1, b='two'),
                          TestStruct(a=3, b='four')])

    def testToJson(self):
        obj = TestStruct(a=100, b='test val')
        result = json.obj_to_string(obj)
        self.assertTrue(result == '{"a": 100, "b": "test val"}' or
                        result == '{"b": "test val", "a": 100}')

    def testReadWrite(self):
        obj = json.read_obj(StringIO.StringIO('{"a": 100, "b": "test val"}'),
                            TestStruct)
        self.assertEqual(obj, TestStruct(a=100, b='test val'))
        out = StringIO.StringIO()
        json.write_obj(out, obj)

        # Simplejson doesn't do deterministic ordering of output elements, so
        # we have to test all permutations.
        result = out.getvalue()
        self.assertTrue(result == '{"a": 100, "b": "test val"}' or
                        result == '{"b": "test val", "a": 100}')

        # Try it with a real file.
        obj = TestStruct(a=100, b='tset val')
        testfile = 'testfile.json'
        json.write_obj(testfile, obj)
        obj2 = json.read_obj(testfile, TestStruct)
        self.assertEqual(obj, obj2)

    def testNestedObjects(self):
        class Outer(confix.Struct):
            inner = confix.FieldDef(TestStruct, 'nested struct type')
            list = confix.FieldDef(confix.List(int), 'nested list')
            map = confix.FieldDef(confix.Map(basestring, int), 'nested map')

        obj = json.string_to_obj('{"inner": {"a": 1, "b": "val"}, '
                                 ' "list": [1, 2, 3], "map": {"a": 1}}', Outer)
        self.assertEqual(obj, Outer(inner=TestStruct(a=1, b='val'),
                                    list=[1, 2, 3],
                                    map={'a': 1}))
        self.assertTrue(isinstance(obj.inner, TestStruct))
        self.assertTrue(isinstance(obj.list, confix.List(int)))
        obj2 = json.string_to_obj(json.obj_to_string(obj), Outer)
        self.assertEqual(obj, obj2)


if __name__ == '__main__':
    unittest.main()
