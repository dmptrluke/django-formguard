# Changelog

## 0.9.1

- Improve PyPI metadata: add project URLs (Issues, Changelog), keywords, and SPDX license format
- Enable digital attestations in the release workflow

## 0.9.0

**Breaking:** API stabilization for 1.0.

- `check()` returns `None` instead of `False` for passing checks
- `GuardResult` no longer compares equal to plain strings; use `.reason` to access the failure string
- `GuardResult` equality now includes `.passed` (two results with the same reason but different pass/fail are no longer equal)
- `guard_on_failure` handlers can return `None` to decline and fall through to normal form error rendering
- `guard_data()` fix: passing `form_class` with global checks no longer crashes; `guard_check_options` flows through correctly
- `get_checks()` removed; use `resolve_checks(get_config('CHECKS'))` directly
- `formguard.conf.get_setting` renamed to `get_config` to avoid shadowing `BaseCheck.get_setting`
- `formguard.utils` module removed; bot detection logging is now internal to `GuardedFormMixin`
- `SIGNING_SALT` constant is now internal (`_SIGNING_SALT`)
- `__all__` defined on all public modules
- W002 system check warns when a check's required settings are missing (e.g. Turnstile without `SITE_KEY`)

**Migration:** Custom checks: change `return False` to `return None`. Signal handlers comparing `GuardResult` to strings: use `result.reason == '...'` or `[r.reason for r in results]`. Code importing `get_setting` from `formguard.conf`: rename to `get_config`. Code importing `handle_bot` from `formguard.utils` or `SIGNING_SALT` from `formguard.checks`: remove

## 0.8.3

- Fix build issue.

## 0.8.2

- Fix `guard_check_options` to work with global checks (no longer requires `guard_checks` to be set)

## 0.8.1

- `TurnstileCheck` supports `APPEARANCE` setting (`always`, `execute`, `interaction-only`)
- Fix docs: removed invalid `SIZE: 'invisible'` example (invisible is a sitekey type, not a size)

## 0.8.0

- `guard_check_options` on forms overrides check settings per-form without subclassing
- `BaseCheck` accepts `options` dict; `get_setting()` checks options before Django settings
- `TurnstileCheck` supports `CALLBACK` and `APPEARANCE` settings
- `TurnstileWidget` renders `data-callback` and `data-appearance` attributes when configured

## 0.7.1

- Fix test key bypass to use Cloudflare's actual published test keys (no dash)
- Use correct sitekey length in test settings and docs

## 0.7.0

- `formguard.contrib.turnstile` adds Cloudflare Turnstile verification as a check
- Turnstile widget renders automatically via `{{ form.media }}` and `{{ form.guard_fields }}`
- Server-side token verification via urllib (no third-party dependencies)
- Built-in test key bypass for fast offline testing with `guard_data()`
- Optional client IP forwarding via `FORMGUARD_TURNSTILE_IP_HEADER`
- Configurable widget theme and size

## 0.6.0

**Breaking:** customizable guard failure handling replaces silent reject booleans.

- `guard_on_failure` callable attribute replaces `guard_silent_reject` / `guard_silent_message`
- `reject_silently` handler class in new `formguard.handlers` module
- Docs restructured: `advanced-usage.md` split into `failure-handling.md`, `configuration.md`, and `checks.md`

**Migration:** Replace `guard_silent_reject = True` with `guard_on_failure = reject_silently()`. Replace `guard_silent_message = '...'` with `reject_silently(message='...')`.

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
