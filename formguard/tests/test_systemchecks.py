from django.test import SimpleTestCase, override_settings

from formguard.systemchecks import check_settings


class SystemCheckTests(SimpleTestCase):
    # non-list FORMGUARD_CHECKS produces E001
    @override_settings(FORMGUARD_CHECKS='not.a.list')
    def test_e001_not_a_list(self):
        errors = check_settings()
        assert len(errors) == 1
        assert errors[0].id == 'formguard.E001'

    # unimportable path produces E002
    @override_settings(FORMGUARD_CHECKS=['nonexistent.module.Check'])
    def test_e002_import_failure(self):
        errors = check_settings()
        assert len(errors) == 1
        assert errors[0].id == 'formguard.E002'
        assert 'nonexistent.module.Check' in errors[0].msg

    # importable non-BaseCheck produces E003
    @override_settings(FORMGUARD_CHECKS=['formguard.conf.DEFAULTS'])
    def test_e003_not_a_check(self):
        errors = check_settings()
        assert len(errors) == 1
        assert errors[0].id == 'formguard.E003'

    # two checks with duplicate field names produces E004
    @override_settings(FORMGUARD_CHECKS=[
        'formguard.tests.test_forms.DuplicateFieldCheckA',
        'formguard.tests.test_forms.DuplicateFieldCheckB',
    ])
    def test_e004_duplicate_fields(self):
        errors = check_settings()
        assert len(errors) == 1
        assert errors[0].id == 'formguard.E004'
        assert 'duplicate_field' in errors[0].msg

    # empty list produces W001
    @override_settings(FORMGUARD_CHECKS=[])
    def test_w001_empty_list(self):
        errors = check_settings()
        assert len(errors) == 1
        assert errors[0].id == 'formguard.W001'

    # valid config produces no errors
    @override_settings(FORMGUARD_CHECKS=[
        'formguard.checks.FieldTrapCheck',
        'formguard.checks.TokenCheck',
    ])
    def test_valid_config(self):
        errors = check_settings()
        assert errors == []

    # no FORMGUARD_CHECKS set produces no errors or warnings
    def test_default_config_no_warnings(self):
        errors = check_settings()
        assert errors == []
