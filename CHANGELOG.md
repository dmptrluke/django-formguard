# Changelog

## 0.5.0

**Breaking:** structured check results, signal rework, consistent `guard_` prefix.

- `GuardResult` objects replace plain strings on `guard_failures` and `guard_results`, carrying `.check`, `.reason`, and `.passed`
- `guard_failed` and `guard_checked` signals replace `guard_triggered`
- `guard_checks`, `guard_silent_reject`, `guard_silent_message` replace old attribute names
- `BUILTINS` constant and `default_checks(include=, exclude=)` helper
- Django system checks validate `FORMGUARD_CHECKS` at startup (E001-E004, W001)
- i18n support on `BaseCheck.message`

## 0.4.0

**Breaking:** guard checks run as form validation inside `is_valid()`. Silent reject replaces `is_bot()`/`bot_response()`. `@guard_form` decorator removed.

## 0.3.0

`InteractionCheck` added, enabled by default.

## 0.2.0

**Breaking:** class-based check pipeline. `BaseCheck` subclasses replace functions. Per-form check overrides, `fail_open`, check-scoped settings.

## 0.1.0

Initial release. `GuardedFormMixin`, `GuardedFormViewMixin`, pluggable check pipeline, built-in checks, `guard_triggered` signal, test helpers.
