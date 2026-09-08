# tests.storybook

Stories for the dashboard's happy paths, one per scenario. **Skeletons — they do not run yet.**

## Does Storybook make sense for React here?

Yes, and more than for most stacks: our components take props as classes and the repository is the
only way they reach data, so a story is just "construct props, render, assert". The `play` functions
also give real user interaction — `userEvent.keyboard('{Meta>}{Enter}{/Meta}')` genuinely exercises
Cmd+Enter, which no unit test of `KeyCommands` can prove end to end.

## Why they don't run

Storybook is not installed, and I don't install without asking. It needs:

```
npm i -D @storybook/react-vite @storybook/test storybook
```

That is a large dev dependency (hundreds of transitive packages). The lighter option that covers three
of the four stories is **vitest + @testing-library/react + jsdom**, which is a fraction of the size and
also unblocks `tests/*.pending`. Storybook additionally gives you the visual sandbox for designing
components, which vitest does not.

Say which you want and I'll install it.

## The mock is at `fetch`, deliberately

`fakeApi.ts` stubs `globalThis.fetch`, not the repository. Two reasons:

- Faking the repository would skip the mapping from wire shapes to domain models — precisely where a
  renamed field or an unexpected enum value bites. With fetch stubbed, the real `EmailRepository`,
  real `Email`/`EmailThread` construction and the real runtime shape guards all run, so every story
  doubles as a contract test against `responses.ts`.
- `EmailRepository` constructs its own client and has no injection point, by design. Stubbing fetch
  avoids putting a seam back into production code purely to serve tests.

`FakeApi` records `markReadCalls` and `replyCalls`, so a story can assert the interaction happened
rather than just that the DOM changed.

## Two stories are pending features

`FilteringByAgentSession` needs the session dropdown (UI-10) and names the selectors it should expose.
`ComposingToASession` needs a compose surface, which UI-10 defers and UI-9's send path underpins.
