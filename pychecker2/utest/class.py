from pychecker2.TestSupport import WarningTester
from pychecker2 import ClassChecks

class ClassTestCase(WarningTester):
    def testClassChecks(self):
        self.silent('class A:\n'
                    '  def f(self):\n'
                    '    return 0\n'
                    'class B(A):\n'
                    '  def g(self):\n'
                    '    return self.f\n')
    def testSelf(self):
        w = ClassChecks.AttributeCheck.missingSelf
        self.warning('class C:\n'
                     '  def f(): pass\n', 2, w, 'f')

    def testSignature(self):
        w = ClassChecks.AttributeCheck.signatureChanged
        self.silent('class Base:\n'
                    '  def f(self): pass\n'
                    'class Derived(Base):\n'
                    '  def f(self): pass\n')
        self.warning('class Base:\n'
                     '  def f(self): pass\n'
                     'class Derived(Base):\n'
                     '  def f(self, x): pass\n',
                     4, w, 'f', 'Base')

    def testUnknownAttribute(self):
        w = ClassChecks.AttributeCheck.unknownAttribute
        self.warning('class C:\n'
                     '  def f(self): return self.x\n', 2, w, 'C', 'x')
        self.silent('class C:\n'
                    '  def f(self): return self.x\n'
                    '  def g(self, v): self.x = v\n')
        self.silent('class D:\n'
                    '  def __init__(self): self.x = 1\n'
                    'class C(D):\n'
                    '  def f(self): return self.x\n')
        imp = '\n\nimport'
        frm = '\n\nfrom'
        import_abuse = [
            (imp, 'pychecker2.utest.data', 'pychecker2.utest.data.Data'),
            (imp, 'pychecker2.utest.data as F',             'F.Data'),
            (frm, 'pychecker2.utest import data',           'data.Data'),
            (frm, 'pychecker2.utest import data as F',      'F.Data'),
            (frm, 'pychecker2.utest.data import Data',      'Data'),
            (frm, 'pychecker2.utest.data import Data as F', 'F'),
            ('class A:\n  class B:\n    import pychecker2.utest.data',
             '',
             'A.B.pychecker2.utest.data.Data'),
            ('class A:\n'
             '  class B:\n'
             '    from pychecker2.utest import data as F',
             '',
             'A.B.F.Data')
            ]
        for fmt in import_abuse:
            self.silent('%s %s\n'
                        'class C(%s):\n'
                        '  def f(self): return self.value\n' % fmt)
            self.silent('%s %s\n'
                        'def g(v):\n'
                        '  class C(%s):\n'
                        '    def f(self): return self.value\n'
                        '  return C(v)\n' % fmt)
            self.warning('%s %s\n'
                         'class C(%s):\n'
                         '  def value(self): pass\n' % fmt,
                         6, ClassChecks.AttributeCheck.methodRedefined,
                         'value', 5, 'C')

            self.warning('%s %s\n'
                         'def g(v):\n'
                         '  class C(%s):\n'
                         '    def value(self): pass\n'
                         '  return C(v)\n' % fmt,
                         6, ClassChecks.AttributeCheck.methodRedefined,
                         'value', 6, 'C')
            self.warning('%s %s\n'
                         'class C(%s):\n'
                         '  def get_value(self, x): pass\n' % fmt,
                         5, ClassChecks.AttributeCheck.signatureChanged,
                         'get_value', 'Data')

    def testSpecial(self):
        for fmt in [('__del__', 'self, args', 1),
                    ('__cmp__', 'self', 2),
                    ]:
            self.warning('class C:\n'
                         '  def %s(%s):\n'
                         '     pass\n' % fmt[0:2],
                         2, ClassChecks.AttributeCheck.specialMethod,
                         fmt[0], fmt[2], fmt[2] > 1 and "s" or "")
        for fmt in [('__del__', 'self'),
                    ('__ge__', 'self, a, b = None, c = None'),
                    ]:
            self.silent('class C:\n'
                         '  def %s(%s):\n'
                         '     pass\n' % fmt)
        self.warning('class C:\n'
                     '  def __not_special__(self):\n'
                     '     pass\n',
                     2, ClassChecks.AttributeCheck.notSpecial,
                     '__not_special__')

    def testUncheckableAttribute(self):
        # inherit from local variable
        self.silent('def f(klass):\n'
                    '  class C(klass):\n'
                    '      def f(self, x):\n'
                    '          self.foo = x\n'
                    '  return C()\n')
        # inherit from an expression
        self.silent('class A:\n'
                    '  def __add__(self, unused):\n'
                    '     return A\n'
                    'class B(A): pass\n'
                    'class C(A() + B()): pass\n')
        # inherit from something not in a source module
        self.warning('import exceptions\n'
                     'class C(exceptions):\n'
                     '  def f(self):\n'
                     '    return self.value\n',
                     4, ClassChecks.AttributeCheck.unknownAttribute,
                     'C', 'value')
        self.warning('import pychecker2.utest.data\n'
                     'class C(pychecker2.utest.data.exceptions.AssertionError):\n'
                     '  def f(self):\n'
                     '    return self.value\n',
                     4, ClassChecks.AttributeCheck.unknownAttribute,
                     'C', 'value')
        self.warning('from pychecker2.utest.data import Data as F\n'
                     'class C(F.DataError):\n'
                     '  def f(self):\n'
                     '    return self.value\n',
                     4, ClassChecks.AttributeCheck.unknownAttribute,
                     'C', 'value')
        self.silent('def f():\n'
                    '   class Foo(None.__class__): pass\n'
                    '   return Foo()\n')