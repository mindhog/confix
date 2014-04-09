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


class OuterStruct(confix.Struct):
    inner = confix.FieldDef(confix.Struct, 'nested struct')


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
        self.assertEqual(t.a, 1)
        self.assertEqual(t.b, 'string')

    def testUndefinedFields(self):
        t = TestStruct(a=200)
        def GetU():
            return t.u
        self.assertRaises(AttributeError, GetU)
        t.u = 100
        self.assertEqual(t.u, 100)
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
        self.assertEqual(val.a, 100)
        self.assertEqual(val.b, 'default value')

    def testCompare(self):
        self.assertEqual(confix.LooseStruct(a=1, b='foo'),
                          confix.LooseStruct(a=1, b='foo'))
        self.assertNotEquals(confix.LooseStruct(a=1, b='foo'),
                             confix.LooseStruct(a=1, b='foo', c=1.5))

        self.assertEqual(TestStruct(a=100, b='value'),
                          TestStruct(a=100, b='value'))
        self.assertNotEquals(TestStruct(a=100, b='value'),
                             TestStruct(a=100, b='different value'))
        self.assertNotEquals(TestStruct(a=100, b='value'),
                             TestStruct(a=100, b='value', u=0))

        # Verify that default fields are compared correctly.
        self.assertEqual(TestStruct(a=100),
                          TestStruct(a=100, b='default value'))

    def testDir(self):
        self.assertEqual(dir(TestStruct(a=1, b='two')), ['a', 'b'])

    def testNesting(self):
        outer = OuterStruct(inner=TestStruct(a=1, b='two'))
        self.assertEqual(outer, outer)

    def testLists(self):
        class TypeWithLists(confix.Struct):
            l = confix.FieldDef(confix.List(str), 'list of strings', [])

        v = TypeWithLists(l=['eeny', 'meeny', 'miney'])

        self.assertRaises(TypeError, v.l.append, 100)
        self.assertRaises(TypeError, v.l.__setitem__, 0, 100)
        v.l.append('moe')
        self.assertEqual(v.l, confix.List(str)(['eeny', 'meeny', 'miney', 'moe']))
        v.l[0] = 'serious'
        self.assertEqual(v.l, ['serious', 'meeny', 'miney', 'moe'])

    def testMaps(self):
        class TypeWithMaps(confix.Struct):
            m = confix.FieldDef(confix.Map(str, int), 'map of string to int',
                                {})

        v = TypeWithMaps(m={'first': 100, 'second': 200})
        self.assertEqual(v.m, {'first': 100, 'second': 200})
        self.assertEqual(v.m['first'], 100)
        self.assertEqual(sorted(v.m.items()),
                          [('first', 100), ('second', 200)])
        self.assertEqual(sorted(v.m.iteritems()),
                          [('first', 100), ('second', 200)])
        self.assertEqual(sorted(v.m.keys()), ['first', 'second'])
        self.assertEqual(sorted(v.m.iterkeys()), ['first', 'second'])
        self.assertEqual(sorted(v.m.values()), [100, 200])
        self.assertEqual(sorted(v.m.itervalues()), [100, 200])
        v.m['third'] = 300
        self.assertEqual(v.m, {'first': 100, 'second': 200, 'third': 300})
        self.assertRaises(TypeError, v.m.__setitem__, 'boing!')
        v.m = {'a': 1, 'b': 2}
        self.assertEqual(v.m, {'a': 1, 'b': 2})
        def set_bad_val():
            v.m = 'blech!'
        self.assertRaises(TypeError, set_bad_val)

        # Test value conversions
        m = confix.Map(str, confix.List(int))({'a': [1, 2]})
        self.assertEqual(m, {'a': [1, 2]})
        self.assertEqual(m.setdefault('b', [0]), confix.List(int)([0]))
        self.assertEqual(m, {'a': [1, 2], 'b': [0]})
        self.assertEqual(m.setdefault('a', [0]), [1, 2])
        self.assertEqual(m, {'a': [1, 2], 'b': [0]})

        self.assertEqual(m.get('c', [3]), confix.List(int)([3]))
        self.assertEqual(m.get('a', [0]), [1, 2])
        self.assertEqual(m, {'a': [1, 2], 'b': [0]})


if __name__ == '__main__':
    unittest.main()
