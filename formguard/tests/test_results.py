from django.test import SimpleTestCase

from formguard.checks import FieldTrapCheck
from formguard.results import GuardResult


class GuardResultTests(SimpleTestCase):
    # two results with the same reason are equal
    def test_eq_same_reason(self):
        a = GuardResult(reason='honeypot field filled', passed=False)
        b = GuardResult(reason='honeypot field filled', passed=False)
        assert a == b

    # results with different reasons are not equal
    def test_eq_different_reason(self):
        a = GuardResult(reason='honeypot field filled', passed=False)
        b = GuardResult(reason='submitted too fast', passed=False)
        assert a != b

    # result can be compared to a plain string via reason
    def test_eq_string(self):
        r = GuardResult(reason='honeypot field filled', passed=False)
        assert r == 'honeypot field filled'
        assert r != 'something else'

    # comparison to unrelated types returns NotImplemented
    def test_eq_unrelated_type(self):
        r = GuardResult(reason='test', passed=False)
        assert r.__eq__(42) is NotImplemented

    # same-reason results hash identically (usable as set/dict keys)
    def test_hash_same_reason(self):
        a = GuardResult(reason='honeypot field filled', passed=False)
        b = GuardResult(reason='honeypot field filled', passed=True)
        assert hash(a) == hash(b)
        assert len({a, b}) == 1

    # str returns reason when present
    def test_str_with_reason(self):
        r = GuardResult(reason='submitted too fast', passed=False)
        assert str(r) == 'submitted too fast'

    # str falls back to check class name when reason is None
    def test_str_falls_back_to_check_name(self):
        r = GuardResult(check=FieldTrapCheck(), passed=True)
        assert str(r) == 'FieldTrapCheck'

    # str raises TypeError when both reason and check are absent
    def test_str_no_reason_no_check(self):
        r = GuardResult(passed=True)
        with self.assertRaises(TypeError):
            str(r)

    # repr includes reason and passed flag
    def test_repr(self):
        r = GuardResult(reason='test', passed=False)
        assert repr(r) == "GuardResult('test', passed=False)"

    # check_name returns the class name of the attached check
    def test_check_name_with_check(self):
        r = GuardResult(check=FieldTrapCheck(), passed=True)
        assert r.check_name == 'FieldTrapCheck'

    # check_name returns None when no check is attached
    def test_check_name_without_check(self):
        r = GuardResult(passed=True)
        assert r.check_name is None
