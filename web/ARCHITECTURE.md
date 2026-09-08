# web architecture

Four tiers, each talking only to the one below it. The seams are the contract; a tier may be
rewritten freely as long as its seam holds.

```
  pages/            root pages, one per route          app/pages/*.tsx
      |
  components/       presentational, props are classes  components/*.tsx
      |
  EmailRepository   one method per UI use case         repository/EmailRepository.ts
      |
  aimelServerClient one method per endpoint            api/aimelServerClient.ts
      |
  the python api                                       src/adapters/resource/api_responses.py
```

## The seams

**1. Server response ↔ client.** `api/responses.ts` mirrors `api_responses.py` **verbatim** — same
field names, same casing. If they drift, nothing fails until runtime, so verbatim is the rule and
the python file is the source of truth.

**2. Client ↔ repository.** The client returns only `*Response` wire shapes and owns `fetch`. Nothing
above it may call `fetch`, and nothing above it should see a `*Response`.

**3. Repository ↔ pages.** The repository takes minimal arguments, calls the client, and returns
**domain models** — real classes with behaviour, enums instead of booleans. One method per UI use
case, named for the use case rather than the endpoint:

| use case | method | returns |
|---|---|---|
| show the inbox | `listInbox()` | `ThreadSummary[]` |
| open a thread | `openThread(emailUuid)` | `EmailThread` |
| reply to an email | `replyTo(emailUuid, body)` | `EmailThread` (reloaded, so the caller need not) |
| mark an email read | `markRead(emailUuid)` | `Email` |

**4. Pages ↔ components.** A component's props are a class, constructed by the page. A renamed or
missing field then fails where it is built, not silently as a blank in the render.

## Rules that hold across every tier

- Enums, never booleans, for anything with more than one meaningful state.
- Unexpected values fail loudly. An unknown enum string from the server raises rather than
  defaulting, because a silent default shows the user the wrong thing.
- No tier reaches past the one below it.
