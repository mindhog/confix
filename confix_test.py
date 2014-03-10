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

import confix
import unittest


class TestStruct(confix.Struct):
    a = confix.FieldDef(int, 'a field', 100)
    b = confix.FieldDef(str, 'b field', 'default value')
    u = confix.FieldDef(int, 'optional field', confix.Undefined)


class ConfixTests(unittest.TestCase):
    def testLoose(self):
        s = confix.LooseStruct(a = 1, b = 2)
        assert s.a == 1
        assert s.b == 2
        s.x = 100
        assert s.x == 100

    def testStrict(self):
        self.assertRaises(AttributeError, TestStruct, x=2)
        self.assertRaises(TypeError, TestStruct, a='string')

        t = TestStruct(a=1, b='string')
        self.assertEquals(t.a, 1)
        self.assertEquals(t.b, 'string')

    def testUndefinedFields(self):
        t = TestStruct(a=200)
        def GetU():
            return t.u
        self.assertRaises(AttributeError, GetU)
        t.u = 100
        self.assertEquals(t.u, 100)
        def SetUToStr():
            t.u = 'hey now!'
        self.assertRaises(TypeError, SetUToStr)

    def testDefaultTypecheck(self):

        def CreateBadStruct():
            class BadStruct(confix.Struct):
                field = confix.FieldDef(str, default=100)

        self.assertRaises(TypeError, CreateBadStruct)

    def testDefaultValues(self):
        val = TestStruct()
        # Don't rely on comparison, as it could be implemented differently and
        # we test it below.
        self.assertEquals(val.a, 100)
        self.assertEquals(val.b, 'default value')

    def testCompare(self):
        self.assertEquals(confix.LooseStruct(a=1, b='foo'),
                          confix.LooseStruct(a=1, b='foo'))
        self.assertNotEquals(confix.LooseStruct(a=1, b='foo'),
                             confix.LooseStruct(a=1, b='foo', c=1.5))

        self.assertEquals(TestStruct(a=100, b='value'),
                          TestStruct(a=100, b='value'))
        self.assertNotEquals(TestStruct(a=100, b='value'),
                             TestStruct(a=100, b='different value'))
        self.assertNotEquals(TestStruct(a=100, b='value'),
                             TestStruct(a=100, b='value', u=0))

        # Verify that default fields are compared correctly.
        self.assertEquals(TestStruct(a=100),
                          TestStruct(a=100, b='default value'))

    def testDir(self):
        self.assertEquals(dir(TestStruct(a=1, b='two')), ['a', 'b'])

if __name__ == '__main__':
    unittest.main()
