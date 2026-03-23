# Built-in Checks

All built-in checks have `fail_open = True`: if a check raises an unexpected
exception, it is skipped rather than blocking real users.

## FieldTrapCheck

Hidden honeypot field that bots fill in. Real users never see it (hidden via
CSS in `formguard/formguard.css`).

**Settings:**
- `FORMGUARD_FIELD_TRAP_FIELD_NAME` (default: `'website'`) - the HTML field name

**Fail mode:** Triggers when the honeypot field contains any value.

## TokenCheck

Signed timestamp embedded when the form loads. Catches submissions that arrive
too fast (automated) or with a tampered/expired token.

**Settings:**
- `FORMGUARD_TOKEN_MIN_SECONDS` (default: `3`) - submissions faster than this fail
- `FORMGUARD_TOKEN_MAX_SECONDS` (default: `3600`) - tokens older than this expire

**Fail mode:** Triggers on fast submissions, bad signatures, or expired tokens.

## JsChallengeCheck

Embeds a random nonce in the form. JavaScript computes a checksum that the
server verifies. Bots without a JS runtime cannot produce the correct value.

**Settings:** None.

**Fail mode:** Triggers when the JS response is missing or incorrect.

**Media:** Requires `formguard/formguard.js` (loaded via `{{ form.media }}`).

## InteractionCheck

Detects real user interaction via `keydown`, `focusin`, and `pointerdown`
events. Accessible to screen readers (keyboard events count).

**Settings:** None.

**Fail mode:** Triggers when no interaction is detected before submission.

**Media:** Requires `formguard/formguard-ia.js` (loaded via `{{ form.media }}`).
