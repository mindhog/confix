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

import poly
import unittest

class PolyTests(unittest.TestCase):
    def testLoose(self):
        s = poly.LooseStruct(a = 1, b = 2)
        assert s.a == 1
        assert s.b == 2
        s.x = 100
        assert s.x == 100

    def testStrict(self):
        class TestStruct(poly.Struct):
            a = poly.FieldDef(None, int, 'a field', 100)
            b = poly.FieldDef(None, str, 'b field', 200)

        self.assertRaises(AttributeError, TestStruct, x=2)
        self.assertRaises(TypeError, TestStruct, a='string')

        t = TestStruct(a=1, b='string')
        self.assertEquals(t.a, 1)
        self.assertEquals(t.b, 'string')

    def testUndefinedFields(self):
        class TestStruct(poly.Struct):
            a = poly.FieldDef(None, int, 'a field', 100)
            u = poly.FieldDef(None, int, 'optional field', poly.Undefined)

        t = TestStruct(a=200)
        def GetU():
            return t.u
        self.assertRaises(AttributeError, GetU)
        t.u = 100
        self.assertEquals(t.u, 100)
        def SetUToStr():
            t.u = 'hey now!'
        self.assertRaises(TypeError, SetUToStr)


if __name__ == '__main__':
    unittest.main()
