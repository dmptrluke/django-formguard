class GuardResult:
    """Outcome of a single guard check: carries the check instance, reason, and pass/fail status."""

    __slots__ = ('check', 'reason', 'passed')

    def __init__(self, *, check=None, reason=None, passed):
        self.check = check
        self.reason = reason
        self.passed = passed

    @property
    def check_name(self):
        return type(self.check).__name__ if self.check else None

    def __str__(self):
        return self.reason or self.check_name

    def __repr__(self):
        return f'GuardResult({self.reason!r}, passed={self.passed})'

    def __eq__(self, other):
        if isinstance(other, GuardResult):
            return self.reason == other.reason
        if isinstance(other, str):
            return self.reason == other
        return NotImplemented

    def __hash__(self):
        return hash(self.reason)
