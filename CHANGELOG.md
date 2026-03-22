# Changelog

## 0.4.0

**Breaking:** guard checks run as form validation.

- Checks run inside `is_valid()` after field validation, adding to `form.errors` and `form.guard_failures`
- `check(self, form)` replaces `check(self, request, form)` (access `form.request` instead)
- `fail_open` default is now `False`; built-in checks explicitly set `True`
- `BaseCheck.message` for user-facing error text
- `stealth_reject` and `stealth_message` on `GuardedFormViewMixin` replace `is_bot()`/`bot_response()`/`FORMGUARD_SUCCESS_MESSAGE`
- `@guard_form` decorator removed

## 0.3.0

- `InteractionCheck` - detects mouse, keyboard, or touch interaction; accessible to screen readers
- Enabled by default in `FORMGUARD_CHECKS`

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
