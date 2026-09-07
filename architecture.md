# Architecture

Hexagonal. Dependencies point inward: `core` knows `ports` and `domain` and nothing else. Adapters
depend on ports; nothing depends on adapters except `application`, which wires them.

```
application/        runs the server; composition root for IOC and DI
ports/              interfaces implemented by adapters, called by core
domain/             domain objects
core/               business logic; calls ports, never concrete adapters
adapters/
  repository/       anything that touches persistence directly
  client/           clients for an external API or SDK
common/             shared helpers with no domain knowledge
```

## Naming

| Layer | Rule | Example |
|---|---|---|
| `ports/` | `I<DomainModel><AdapterCategory>`, agnostic of implementation | `IEmailRepository` |
| `adapters/repository/` | `<Brand or type><PortName>` | `SqlLiteEmailRepository implements IEmailRepository` |
| `adapters/client/` | `<Brand><PortName>` | `TwitterClient implements ISocialMediaClient` |

A port name must never leak its implementation. `IEmailRepository`, not `ISqlEmailRepository` — the
whole point is that core cannot tell what is behind it.

## The service name is a variable

Source refers to the service as `SERVICE`, resolved from `service_name` in config (`aimel`). Do not
scatter the product name through the code: renaming the service must touch config, not modules. This
extends to anything derived from it, including mail header names, which render as
`X-{SERVICE}-Session` rather than a hardcoded literal.

## Domain north star

- **Non-null fields.** Absence is modelled explicitly, not by a null that every caller must re-check.
- **Strongly typed fields** wherever a primitive would be ambiguous. A `ThreadSlug` is not a `str`.
- **Enums instead of booleans**, because a boolean cannot be extended without a migration and a
  second boolean. Two booleans already encode four states, of which at least one is nonsense.

The message state is the live example. `read: bool` plus `deleted: bool` permits "deleted but unread"
and forces every query to know which combinations are legal:

```
MessageState = UNREAD | READ | DELETED
```

One field, exhaustive, and a new state costs one enum member rather than a schema change.

## Deletion is soft

Deleting sets `deleted_at` and transitions state to `DELETED`. Nothing is removed. A record also
moves out of the live store into the archive store, so the hot path never scans dead rows. The
repository port hides both halves — core calls `delete(id)` and does not know an archive exists.

## Concrete adapters

| Port | Adapter | Category |
|---|---|---|
| `IEmailRepository` | `SqliteEmailRepository` | repository |
| `IEmailTransport` | `SmtpEmailTransport` | client |
| `IMailboxClient` | `MailpitMailboxClient` | client |

Mailpit is a **client**, not a repository — it is an intake spool we drain, not our store.

## Typed models at every boundary

Core only ever sees domain models. Never a dict, never a JSON blob, never a raw string that
"happens to be" an address.

- **Marshal at the edge, immediately.** An `application/` resource turns incoming data into a request
  object on arrival, before any logic runs. Request objects live in `application/` — they are wire
  shapes, not domain concepts, and must not leak inward.
- **The caller constructs the domain object.** Application code builds whatever domain model the core
  method requires and passes that. Core does not parse.
- **Both directions.** Downstream results are marshalled back into domain models too, so an adapter's
  response shape never reaches core.
- **Non-nullable by default.** If a field is optional, that is usually two different shapes wearing
  one name — write two models instead of one with a nullable field.

`@dataclass(frozen=True)` is enough here; Pydantic is fine where real validation earns its weight.

### Where that bites today

`Message` currently carries `read_at: datetime | None` and `deleted_at: datetime | None`, which is
exactly the nullable-field smell above. Three states means three shapes:

| Model | Carries |
|---|---|
| `UnreadMessage` | no state timestamps |
| `ReadMessage` | `read_at`, non-null |
| `DeletedMessage` | `deleted_at`, non-null |

That also lines up one-to-one with the tables, so the repository maps a shape to a table rather than
inspecting an enum and hoping the right columns are populated.

## Storage: this service owns it

Decided. Mailpit stores everything in one `mailbox` table with read state as a `Read` column — no
`deleted_at`, no per-state tables — so the state model cannot be layered onto it.

Mailpit is therefore demoted to an SMTP intake spool. This service drains it into its own SQLite
database at `<mail_dir>/inbox/mail.db`, one table per state:

```
mail.db
  unread   (base columns)
  read     (base columns, read_at)
  deleted  (base columns, read_at, deleted_at)
```

A state change moves the row between tables in one transaction. Deletion is soft: `deleted_at` is
stamped and the row lands in `deleted`, never removed.

Draining does not purge Mailpit yet. Until this service has its own HTML view, Mailpit's UI is the
only way to read mail, so purge stays off to avoid a window with no reader.
