import time

from django.core import signing
from django.test import SimpleTestCase

from formguard.test import GuardedFormTestMixin, make_guard_token


class MakeGuardTokenTests(SimpleTestCase):
    # returns a valid signed token
    def test_returns_valid_token(self):
        token = make_guard_token()
        loaded = signing.loads(token, salt='formguard')
        assert isinstance(loaded, float)

    # token timestamp is in the past (form appears to have loaded long ago)
    def test_token_is_old_enough(self):
        token = make_guard_token()
        loaded = signing.loads(token, salt='formguard')
        assert time.time() - loaded >= 10


class GuardedFormTestMixinTests(GuardedFormTestMixin, SimpleTestCase):
    # guard_data returns dict with empty honeypot and valid token
    def test_guard_data_keys(self):
        data = self.guard_data()
        assert 'website' in data
        assert 'fg_token' in data
        assert data['website'] == ''

    # token in guard_data is valid
    def test_guard_data_token_valid(self):
        data = self.guard_data()
        loaded = signing.loads(data['fg_token'], salt='formguard')
        assert isinstance(loaded, float)

    # guard_data includes JS challenge with correct computed value
    def test_guard_data_includes_js_challenge(self):
        data = self.guard_data()
        assert 'fg_js' in data
        token = data['fg_token']
        expected = format(sum(ord(c) for c in token) & 0xFFFF, 'x')
        assert data['fg_js'] == expected
