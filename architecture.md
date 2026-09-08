# Architecture

Hexagonal. Dependencies point inward: `core` knows `ports` and `domain` and nothing else. Adapters
depend on ports; nothing depends on adapters except `application`, which wires them.

```
src/
  application/
    main.py                   entrypoint; owns the singletons for the process lifetime
    cli_request_marshaller.py argv -> typed requests, at the edge
    module_dependencies/      one module per adapter group
      application_module.py   composition root
      database_module.py      owns the driver session factory
      repository_module.py    provides repositories over the db client
      client_module.py        provides transport and spool clients
      core_module.py          provides services
      common_module.py        naming, session lookup, rendering, colour
  ports/                      interfaces implemented by adapters, called by core
  domain/                     domain objects
  core/                       business logic; calls ports, never concrete adapters
  adapters/
    database/                 wraps the driver, holds the session, executes SQL
    repository/               composes SQL, delegates execution to the database adapter
    client/                   clients for an external API or SDK
    resource/                 upstream adapters plus their request objects
  common/                     shared collaborators with no domain knowledge
test/                         mirrors src/, plus fixtures/ and helpers/
```

`test/` has the same shape as `src/` so a file's tests are findable by path alone. Run with
`uv run python -m unittest discover -s test -t .`.

## Classes, not scripts

Everything is a class instantiated once in the composition root and injected — `ConfigLoader`,
`NamingPolicy`, `SessionDetector`, `ThreadRenderer`, `SessionColorPalette`, `CliApplication`.
Module-level functions are avoided because they cannot be substituted without monkeypatching, which
is what makes the tests below possible: the real class under test, spec'd mocks for its
collaborators, and no patching anywhere.

## Composition root

No DI framework. Modules are plain classes wired by hand in dependency order, each one responsible
for building its own adapter from config, and each `provide_*` returning a port rather than a
concrete type.

```python
class ApplicationModule:
    def __init__(self, config: AppConfig):
        self.database_module = DatabaseModule(config.database)
        self.repository_module = RepositoryModule(self.database_module.provide_database_client())
        self.client_module = ClientModule(config.smtp, config.mailbox, config.naming.service_name)
        self.core_module = CoreModule(
            self.repository_module.provide_email_repository(),
            self.client_module.provide_email_transport(),
            self.client_module.provide_mailbox_client(),
        )
```

Two rules that keep this honest:

- **A module takes ports, not other modules.** `RepositoryModule` receives an `IDatabaseClient`, not
  the `DatabaseModule`, so it cannot reach past the interface to the raw connection.
- **The repository never opens a connection.** `DatabaseModule` calls
  `sqlite_database_client.start(...)` once; the repository composes SQL and hands it to the client.
  That split is why swapping SQLite for anything else touches one module.

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
covers addresses and subjects (`NamingConfig`, `NamingPolicy`). Mail header names are the one
exception: they are hardcoded constants in `MailHeaders` (`src/common/headers.py`), not derived from
`service_name`, so a rename never silently detaches the writer's headers from the reader's.

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

### The shapes

| Model | Carries |
|---|---|
| `NewCorrespondence` | no `id`, no `created_at` — not yet persisted |
| `Correspondence` | `id` (uuid) and `created_at`, both assigned by the schema |
| `UnreadMessage` | no state timestamp |
| `ReadMessage` | `read_at`, non-null |
| `DeletedMessage` | `deleted_at` and `previous_state`, both non-null |

`DeletedMessage` records `previous_state` rather than a nullable `read_at`, because a message deleted
while unread has no read time and `read_at = ''` is a null wearing a costume.

Primitives do not cross boundaries either. An address is an `Email` value object with an `address`
field, so validation has somewhere to live as it grows; adapters unwrap it at the very edge when
writing a bind or a wire header. Request objects are built once by `CliRequestMarshaller` with
`SessionId`, `ThreadSlug` and `Author` already parsed, so no downstream code re-parses a string.

## Identity: uuid out, primary key in

Every table has both a surrogate `pk INTEGER PRIMARY KEY AUTOINCREMENT` and a
`uuid TEXT NOT NULL UNIQUE`, defaulted by the schema (SQLite has no `uuid()`, so it is composed from
`randomblob`). The **primary key never leaves the repository** — domain objects expose the uuid as
`id`, and it survives every state change because a move carries the original uuid forward rather
than letting the default generate a new one.

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
