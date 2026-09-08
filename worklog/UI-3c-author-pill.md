# UI-3c — author pill

Status: **not started**

Fill `web/src/components/emailpane/AuthorPill.tsx`. Props are settled; own that file only.

- Background is `participantColor(props.emailAddress)` from `domain/ParticipantColor.ts`. Everyone
  gets one, the human included — the human having no colour while agents do is the current wart.
- `label` is the visible text ("you", "agent", or the address).
- Text must stay legible on whatever colour comes back: pick foreground from the background's
  luminance, do not hardcode white or black.

`participantColor` throws until UI-1 lands. Build against it; do not edit its file.

Done means `npx tsc -b` exits 0 and it renders. Then set Status above to **done** with one line on
anything you decided.
