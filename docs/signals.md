# Signals

Two signals are available, both with the same interface:

- **`guard_failed`** -- fires only when at least one check fails
- **`guard_checked`** -- fires after every check run, regardless of outcome

```python
from formguard.signals import guard_failed, guard_checked

def on_guard_failed(sender, request, form, results, **kwargs):
    for r in results:
        if not r.passed:
            log_failure(r.reason, r.check_name)

def on_guard_checked(sender, request, form, results, **kwargs):
    for r in results:
        metrics.increment(
            f'guard.{r.check_name}',
            tags={'passed': r.passed},
        )

guard_failed.connect(on_guard_failed)
guard_checked.connect(on_guard_checked)
```

## Arguments

| Argument | Description |
| -- | -- |
| `sender` | The form class |
| `request` | The current `HttpRequest` |
| `form` | The bound form instance |
| `results` | List of `GuardResult` objects from all checks that ran |

Each entry in `results` is a `formguard.results.GuardResult`:

| Attribute | Description |
| -- | -- |
| `reason` | The reason string (e.g. `'honeypot field filled'`), or `None` for passed checks |
| `check` | The check instance that produced this result |
| `check_name` | The check class name (e.g. `'FieldTrapCheck'`) |
| `passed` | `True` if the check passed, `False` if it triggered |

`GuardResult` compares equal to its reason string, so `'honeypot field filled' in results` works.
`str(result)` returns the reason string for failures, or the check class name for passes.
