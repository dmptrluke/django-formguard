# Signals

## guard_triggered

Emitted during `is_valid()` whenever a submission is flagged by guard checks.
Use it for logging, monitoring, or rate limiting.

```python
from formguard.signals import guard_triggered

def on_guard_triggered(sender, request, form, reasons, **kwargs):
    # log to monitoring, increment counter, etc.
    pass

guard_triggered.connect(on_guard_triggered)
```

Arguments:

| Argument | Description |
| -- | -- |
| `sender` | The form class |
| `request` | The current `HttpRequest` |
| `form` | The bound form instance |
| `reasons` | List of reason strings from triggered checks |
