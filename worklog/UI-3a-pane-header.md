# UI-3a — pane header

Status: **not started**

Fill `web/src/components/emailpane/PaneHeader.tsx`. Props are settled; own that file only.

- The AI session's **full** uuid, not the 8-char short form. The short form is for the narrow list;
  in the pane there is room and the full one is what you paste into a `claude --resume`.
- The subject below it.
- Keep the existing session-chip colour treatment (`--color-*` tokens, `.chip`); the pane is the one
  place the full id appears, so it should still read as the same thing as the chip in the list.

Done means `npx tsc -b` exits 0 and it renders. Then set Status above to **done** with one line on
anything you decided.
