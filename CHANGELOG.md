# Changelog

## 0.1.0

Initial release.

- `GuardedFormMixin` for adding guard fields to forms
- `GuardedFormViewMixin` for CBV bot detection
- `@guard_form` decorator for FBV bot detection (auto-reject and annotate modes)
- Built-in checks: `field_trap`, `timing`, `signature`, `js_challenge`
- `guard_triggered` Django signal
- `HoneypotWidget` with CSS hiding and JS support
- `GuardedFormTestMixin` and `make_guard_token()` test helpers
- Pluggable check pipeline via `FORMGUARD_CHECKS` setting
