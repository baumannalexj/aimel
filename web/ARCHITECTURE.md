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

## Errors

Errors change shape at every seam, deliberately. Each tier translates rather than leaking.

```
  aimelServerClient   ->  Result<T, ResponseError>    exhaustive, compiler-checked
  EmailRepository     ->  throws DomainException      switches on ResponseError.kind
  root container      ->  toast / red banner          catches DomainException
```

**Client returns a Result, it does not throw.** `Result<T, ResponseError>` is a discriminated union
(no library — it is about fifteen lines). The reason is exhaustiveness: the repository must handle
every `ResponseError` variant or the compiler complains. A thrown error is invisible to the type
checker, so a new failure mode would silently fall through to whatever catch-all exists. The client
logs before returning an `Err`, so the raw HTTP detail is on the console exactly once.

`ResponseError` variants, each with a `kind` discriminant plus status and path:

| kind | when |
|---|---|
| `Unreachable` | fetch itself failed — the api is not running |
| `NotFound` | 404 |
| `Conflict` | 409, e.g. marking a deleted email read |
| `Invalid` | 422, e.g. an empty reply body |
| `ServerFault` | 5xx |
| `Malformed` | 2xx whose body did not parse as the expected shape |

**Repository throws, it does not return a Result.** It switches on `kind` and raises a
`DomainException` phrased for a human. Pages and components must not thread Results through render
code — that is what makes view code unreadable — so propagation becomes an exception again here.

**The root container is the only place that renders an error.** It catches `DomainException` and
shows a toast or a red banner. No component decides how to display a failure, and no component
swallows one.

Anything that is not a `DomainException` reaching the root container is a bug, not a user-facing
message: log it and show something generic, because an unmapped error means a seam was skipped.
