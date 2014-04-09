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

from StringIO import StringIO
import unittest
import confix
from confix import yaml


class TestObj(confix.Struct):
    first = confix.FieldDef(int, 'first field')
    second = confix.FieldDef(str, 'second field')
    list = confix.FieldDef(confix.List(int), 'test list', default=confix.Undefined)
    map = confix.FieldDef(confix.Map(str, int), 'test map', default=confix.Undefined)


class YAMLTest(unittest.TestCase):

    def testBasics(self):
        string_rep = '{first: 100, second: some value}\n'
        obj = yaml.string_to_obj(string_rep, TestObj)
        self.assertEqual(obj, TestObj(first=100, second='some value'))
        self.assertEqual(yaml.obj_to_string(obj), string_rep)

    def testReadWrite(self):
        out = StringIO()
        init_obj = TestObj(first=100, second='data', list=[1, 2, 3],
                           map={'foo': 1, 'bar': 2})
        yaml.write_obj(out, init_obj)
        result = yaml.read_obj(StringIO(out.getvalue()), TestObj)
        self.assertEqual(result, init_obj)

    def testDefaultConversions(self):
        obj = yaml.string_to_obj('{first: 100, second: some value}')
        self.assertEqual(obj,
                         confix.LooseStruct(first=100, second='some value'))

if __name__ == '__main__':
    unittest.main()
