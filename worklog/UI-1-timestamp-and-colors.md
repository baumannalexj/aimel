# UI-1 — timestamp display + per-participant pill colour

Fill in two seams. Pure functions, no React, no fetch.

## `domain/Timestamp.ts`

`display()`, in the browser's timezone, 24h:

```
same year      wed 9/7 @ 14:33
different year 2024/9/7 @ 14:33
```

Lowercase weekday, no leading zeros on month/day, `@` separator. When the year is not the current
year the weekday is *replaced* by the year — it is not appended.

## `domain/ParticipantColor.ts`

`hashToHex(seed)` → stable hex, same seed same colour forever. `participantColor(email)` already
normalises and delegates; leave it.

Everyone gets one, the human included.

**Judgment call to make and report:** a raw hash mapped straight to 24 bits produces unreadable
pills (near-white on white, muddy browns). `src/common/session_color.py` has a Paul Tol
colourblind-safe palette already chosen for this app. Prefer hashing to an index into that palette,
ported to TS, so output stays readable — the function still returns hex and is still deterministic.
If you disagree, say why.

## Done means

Tests for both. Same-year and cross-year timestamps; a stability test that the same email yields the
same colour across calls; a spread check that a handful of realistic addresses
(`alexander.baumann@aimel.com`, `claude-0bd9c0c5@aimel.com`, …) don't all collide onto one colour.
`npx tsc -b` exits 0.
