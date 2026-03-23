# Cloudflare Turnstile

`formguard.contrib.turnstile` adds Cloudflare Turnstile verification as a
formguard check. No third-party dependencies beyond Django.

## Setup

Get your site key and secret key from the
[Cloudflare dashboard](https://dash.cloudflare.com/?to=/:account/turnstile).

Add the settings:

```python
FORMGUARD_TURNSTILE_SITE_KEY = 'your-site-key'
FORMGUARD_TURNSTILE_SECRET_KEY = 'your-secret-key'
```

Register the check globally:

```python
from formguard.conf import BUILTINS
FORMGUARD_CHECKS = BUILTINS + [
    'formguard.contrib.turnstile.TurnstileCheck',
]
```

Or per-form with `guard_checks`:

```python
from formguard.conf import default_checks

class SignupForm(GuardedFormMixin, forms.Form):
    guard_checks = default_checks(include=['formguard.contrib.turnstile.TurnstileCheck'])
    ...
```

Templates work the same as any guarded form. `{{ form.media }}` loads the
Cloudflare script, and the Turnstile widget renders automatically with
`{{ form }}` or `{{ form.guard_fields }}`.

## Settings

| Setting | Default | Purpose |
|---|---|---|
| `FORMGUARD_TURNSTILE_SITE_KEY` | (required) | Cloudflare site key |
| `FORMGUARD_TURNSTILE_SECRET_KEY` | (required) | Cloudflare secret key |
| `FORMGUARD_TURNSTILE_THEME` | `'auto'` | Widget theme: `auto`, `light`, `dark` |
| `FORMGUARD_TURNSTILE_SIZE` | `'normal'` | Widget size: `normal`, `compact` |
| `FORMGUARD_TURNSTILE_TIMEOUT` | `5` | Seconds before the Cloudflare verification request times out |
| `FORMGUARD_TURNSTILE_CALLBACK` | `None` | JS function name called when verification completes |
| `FORMGUARD_TURNSTILE_IP_HEADER` | `None` | `request.META` key for client IP forwarding (see below) |

## Per-form options

Use `guard_check_options` to configure Turnstile differently per form. For
an invisible interstitial that auto-submits on verification:

```python
class InterstitialForm(GuardedFormMixin, forms.Form):
    guard_checks = [
        'formguard.contrib.turnstile.TurnstileCheck',
    ]
    guard_check_options = {
        'formguard.contrib.turnstile.TurnstileCheck': {
            'SIZE': 'invisible',
            'CALLBACK': 'onTurnstileComplete',
        },
    }
```

See [Configuration](configuration.md) for how `guard_check_options` works.

## IP forwarding

By default, the client IP is not sent to Cloudflare during verification. To
enable it, set `IP_HEADER` to the `request.META` key containing the client IP:

```python
# behind Cloudflare proxy
FORMGUARD_TURNSTILE_IP_HEADER = 'HTTP_CF_CONNECTING_IP'

# behind a standard reverse proxy
FORMGUARD_TURNSTILE_IP_HEADER = 'HTTP_X_FORWARDED_FOR'

# direct connection
FORMGUARD_TURNSTILE_IP_HEADER = 'REMOTE_ADDR'
```

For headers that contain comma-separated IPs (like `X-Forwarded-For`), the
leftmost entry is used.

## Testing

Cloudflare publishes test keys that skip real verification. Configure them in
your test settings:

```python
FORMGUARD_TURNSTILE_SITE_KEY = '1x00000000000000000000AA'
FORMGUARD_TURNSTILE_SECRET_KEY = '1x0000000000000000000000000000000AA'
```

With test keys configured, `guard_data()` works without network access:

```python
from formguard.test import GuardedFormTestMixin

class SignupViewTests(GuardedFormTestMixin, TestCase):
    def test_valid_signup(self):
        data = {'username': 'alice', 'email': 'a@b.com', **self.guard_data()}
        response = self.client.post('/signup/', data)
        assert response.status_code == 302
```

The test key bypass is built into `verify_token()`. Cloudflare's always-pass
secret key skips HTTP and returns success; the always-fail and token-spent keys
return failure. No mocking needed.

## Async views

`TurnstileCheck.check()` makes a synchronous HTTP call via `urllib`. In async
views, wrap the form validation with `sync_to_async`:

```python
from asgiref.sync import sync_to_async

valid = await sync_to_async(form.is_valid)()
```

## Customization

For widget configuration (theme, size, callback), use `guard_check_options`
on the form (see above). For deeper customization, subclass `TurnstileCheck`:

```python
from formguard.contrib.turnstile import TurnstileCheck

class ConditionalTurnstileCheck(TurnstileCheck):
    def check(self, form):
        if is_trusted_ip(form.request):
            return False
        return super().check(form)
```

Register the subclass instead of `TurnstileCheck` in your settings or
`guard_checks`.
