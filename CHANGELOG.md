# Changelog

## 0.2.1

- `guard_fields` property on `GuardedFormMixin` for templates that render fields manually

## 0.2.0

**Breaking:** class-based check pipeline.

- Checks are now `BaseCheck` subclasses that own their fields, media, settings, and test data
- `FieldTrapCheck`, `TokenCheck`, `JsChallengeCheck` replace the old functions
- `TokenCheck` merges the old `timing` and `signature` checks
- `JsChallengeCheck` uses its own nonce instead of the signed token
- `GuardedFormMixin` aggregates fields from checks instead of hardcoding them
- Per-form `formguard_checks` attribute to override global checks on specific forms
- `guard_data(form_class=...)` for testing forms with per-form checks
- Per-check `fail_open` attribute for fail-closed checks (e.g. CAPTCHA)
- Check-scoped settings via `settings_prefix` and `defaults`
- Documentation split into `docs/` (custom checks, advanced usage, testing, signals)
- `make_guard_token()` removed

**Migrating:**

- `FORMGUARD_CHECKS` paths changed:
  - `field_trap` -> `FieldTrapCheck`
  - `timing` + `signature` -> `TokenCheck`
  - `js_challenge` -> `JsChallengeCheck`
- Settings renamed: `FORMGUARD_FIELD_NAME` -> `FORMGUARD_FIELD_TRAP_FIELD_NAME`, `FORMGUARD_MIN_SECONDS` -> `FORMGUARD_TOKEN_MIN_SECONDS`, `FORMGUARD_MAX_SECONDS` -> `FORMGUARD_TOKEN_MAX_SECONDS`
- Custom checks must subclass `BaseCheck` instead of being plain functions

## 0.1.1

- Move success message from `is_bot()` to `bot_response()` so calling `is_bot()` has no user-visible side effects

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
