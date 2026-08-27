---
name: python-architecture
description: Interface-first, dependency-injected Python architecture - Protocols and Pydantic models in an `interfaces` package, implementations in a mirroring `modules` package, one class per file, IO confined to edge modules, everything constructor-injected, fully testable in memory. Use when starting a new Python project, deciding how to structure one, or reviewing existing Python code against a consistent architecture.
---

# Interface-first Python architecture

This skill is **reference information**, not a script. It describes one consistent way to structure
a Python project. Load it, then decide what to do with it: scaffold a new project, refactor an
existing one toward it, or review code against it. It does not write files on its own.

The goal it optimises for is **testability without IO**. Every piece of logic can be exercised in
memory, with no filesystem, no clock, no terminal and no network, because the few places that
genuinely touch the outside world are isolated behind interfaces and injected in.

---

## 1. Principles

1. **An interface in front of every module.** Each module exposes a `typing.Protocol`. Consumers
   depend on the Protocol, never on a concrete class.
2. **Modules are free from IO.** Only designated *edge* modules touch the outside world. Everything
   else is pure.
3. **Everything is dependency-injected.** No class constructs its own collaborators. No globals, no
   module-level singletons, no service locators. Dependencies arrive through `__init__`.
4. **Fully type hinted.** `mypy --strict` passes on both source and tests.
5. **Testing is a core philosophy, not an afterthought.** Pure classes are unit-testable with no IO
   at all; the whole application runs in memory against fakes.
6. **Frontends are thin.** A CLI, a web API, a queue consumer - each is an adapter that parses input
   and calls the facade. Zero business logic.
7. **Interfaces and implementations are physically separated.** `interfaces/` holds only Protocols,
   models and enums - no behaviour. `modules/` may import `interfaces/`; the reverse is forbidden.
8. **One public class per file.** The filename is the class name in snake_case: `FileSystem` lives in
   `file_system.py`, `LocalFileSystem` in `local_file_system.py`. The only thing that may share a
   file with a class is a private helper used solely by that class.

---

## 2. Layout

```
pyproject.toml
src/<project>/
  __init__.py
  container.py                   # dependency-injector wiring
  interfaces/                    # Protocols + models ONLY. No behaviour.
    __init__.py
    <domain>/
      __init__.py                # re-exports this domain's public names
      <interface_name>.py        # one Protocol
      <model_name>.py            # one Pydantic model
    engine/
      engine.py                  # Engine (Protocol) - the facade
  modules/                       # implementations, mirroring interfaces/
    __init__.py
    <domain>/
      __init__.py
      <impl_name>.py             # one class
    engine/
      default_engine.py
  cli/                           # OPTIONAL frontend
    main.py                      # the ONLY place the container is instantiated
tests/
  fakes/                         # one fake per file: InMemoryX, FrozenY
  unit/                          # per-class, pure, in-memory
  integration/                   # facade end-to-end with fakes; frontend smoke tests
```

A `<domain>` is a capability: `file_system`, `clock`, `console`, `log`, `http`, `config`, `store`.
Both trees use the same domain names so an interface and its implementations are one directory apart.

**Dependency direction, strictly one way:**

```
frontend  ->  container  ->  modules  ->  interfaces
```

Nothing under `interfaces/` imports from `modules/`, `cli/`, or any frontend. That rule is what keeps
`interfaces/` importable, cheap, and free of side effects.

---

## 3. Naming

- Interfaces carry **no `I` prefix**. The plain noun is the interface: `FileSystem`, `Clock`, `Store`.
- Implementations carry a **qualifying prefix** that says what kind they are:
  `LocalFileSystem`, `SystemClock`, `StdioConsole`, `PostgresStore`, `DefaultEngine`,
  and in tests `InMemoryFileSystem`, `FrozenClock`.
- Each sub-package's `__init__.py` re-exports its public names, and that is the import surface.
  Import from the sub-package, never from the leaf file:

  ```python
  from <project>.interfaces.file_system import FileInfo, FileSystem
  from <project>.modules.file_system import LocalFileSystem
  ```

---

## 4. Edge modules

An edge module is one whose whole job is to talk to something outside the process. Typically:

| Domain | Why it is an edge |
|---|---|
| `file_system` | reads and writes real files |
| `clock` | reads the wall clock - **non-deterministic**, so it must be injectable |
| `console` | writes to stdout/stderr |
| `http` | network calls |
| `environment` | reads env vars and process arguments |
| `process` | spawns subprocesses |
| `store` | database access |

The clock is the one people forget. `datetime.now()` buried in a pure class makes its output
untestable, so time arrives through `Clock.now()` like any other dependency.

**The rule:** no `print()`, `open()`, `datetime.now()`, `os.environ`, `requests`/`httpx` calls, or
`subprocess` anywhere outside the edge modules. This is greppable, and worth grepping for in review.

Edge implementations stay thin - they translate and delegate, nothing more. Any logic worth testing
belongs in a pure class that receives the edge through its interface.

---

## 5. Models

Models are **Pydantic** and live in `interfaces/<domain>/`, beside the Protocol that uses them:

```python
class FileInfo(BaseModel):
    """Metadata about a single filesystem entry."""

    model_config = ConfigDict(frozen=True)

    path: Path
    size_bytes: int
    modified_at: datetime
    is_directory: bool
```

- **Frozen.** `ConfigDict(frozen=True)` everywhere. Immutable values are safe to pass around and
  trivially comparable in assertions.
- **Data only.** No behaviour, no IO, no dependencies on `modules/`.
- **Prefer stdlib types.** Use `pathlib.Path`, `datetime`, `Decimal`, `StrEnum`. Do not invent a
  wrapper for something the standard library already names well - a custom `Path` class buys nothing
  and shadows a name every reader already knows.
- Enums are `StrEnum` and get their own file, same as classes.

---

## 6. The facade

One Protocol - conventionally `Engine` - is the single entry point into the application:

```python
class Engine(Protocol):
    """The facade every frontend calls. All behaviour of the application hangs off this."""

    def start(self) -> None: ...
```

Every use case is a method on it. Frontends call those methods and do nothing else, which is what
makes a CLI and a web API interchangeable adapters over the same core. When a new capability is
added, it becomes an `Engine` method first; the frontend only learns how to invoke it.

`DefaultEngine` takes one constructor parameter per module it needs. When that list gets long, the
answer is to group related capabilities behind an intermediate service interface - not to reach for
a global.

---

## 7. Dependency injection

Use [`dependency-injector`](https://python-dependency-injector.ets-labs.org/). One container declares
every implementation:

```python
class Container(containers.DeclarativeContainer):
    clock = providers.Singleton(SystemClock)
    console = providers.Singleton(StdioConsole)
    file_system = providers.Singleton(LocalFileSystem)
    log_formatter = providers.Singleton(AnsiLogFormatter)
    logger = providers.Singleton(
        DefaultLogger, clock=clock, formatter=log_formatter, console=console
    )
    engine = providers.Singleton(DefaultEngine, logger=logger)
```

- **Exactly one composition root.** The frontend's entry module is the only place `Container()` is
  instantiated. Nothing else may construct it or import from it.
- **Tests never use the production container.** They construct classes directly with fakes, or -
  for an integration test that wants the real wiring - build a container and
  `container.<provider>.override(<fake>)` the edges.

---

## 8. Testing

The architecture exists to make this cheap, so it is worth being deliberate about:

- **Unit tests** cover pure classes with no IO whatsoever. A formatter test asserts on the exact
  string; a policy test asserts on the returned value.
- **Fakes** live in `tests/fakes/`, one per file, and are the in-memory counterparts of the edge
  modules: `InMemoryFileSystem` backed by a `dict[Path, str]`, `InMemoryConsole` collecting a
  `list[str]`, `FrozenClock` returning a constant `datetime`.
- Prefer **fakes over mocks**. A fake with real behaviour catches integration mistakes a mock's
  `assert_called_with` never will, and it stays readable as the interface grows.
- **Integration tests** exercise the whole `Engine` in memory through the fakes, plus a thin smoke
  test of the actual frontend.
- Because the clock is injected, assertions can hardcode timestamps - no `freezegun`, no sleeping,
  no flakiness.

---

## 9. Tooling

A uv project with a `src/` layout:

```
uv sync                       # install
uv run <entrypoint>           # run
uv run pytest                 # test
uv run mypy src tests         # types
uv run ruff check src tests   # lint
```

- Runtime deps: `dependency-injector`, `pydantic` (+ `typer` if there is a CLI).
- Dev deps: `pytest`, `mypy`, `ruff`.
- Enable the Pydantic mypy plugin, or `mypy --strict` will not catch assignment to a frozen field:

  ```toml
  [tool.mypy]
  strict = true
  plugins = ["pydantic.mypy"]
  ```

- Python >= 3.11 for `StrEnum`.
- Point pytest at the repo root (`pythonpath = ["."]`) so `tests.fakes` imports cleanly.

---

## 10. Optional: CLI frontend

Typer, with the entry point declared in `pyproject.toml`:

```toml
[project.scripts]
<command-name> = "<project>.cli.main:main"
```

The command builds the container and calls the engine - nothing else:

```python
app = typer.Typer(no_args_is_help=True)


@app.callback()
def cli() -> None:
    """Keep the app a command group even when there is only one subcommand."""


@app.command()
def start() -> None:
    Container().engine().start()
```

**Gotcha worth knowing:** a Typer app with a *single* `@app.command()` collapses into a bare
command, so `mytool start` fails with exit code 2 - `start` gets parsed as an argument. The empty
`@app.callback()` above forces it to stay a command group. It becomes redundant once a second
subcommand exists, and is harmless to leave in place.

---

## 11. Optional: logging module

Logging is a module like any other, split across four names:

- `LogLevel` - `StrEnum` of DEBUG/INFO/WARNING/ERROR/CRITICAL.
- `LogRecord` - frozen model of `level`, `message`, `timestamp`.
- `LogFormatter` - `format(record) -> str`. **Pure.**
- `Logger` - `debug/info/warning/error/critical(message)`.

`DefaultLogger(clock, formatter, console)` asks the clock for the time, builds a `LogRecord`, asks
the formatter for the line, and hands the string to the console. It is the only class allowed to
depend on `Console`.

Name the package **`log`, not `logging`** - absolute imports make `logging` technically safe, but it
reads ambiguously next to the stdlib module.

For a colored line like `2025-09-10 INFO started`:

- Color **only the level token**, never the timestamp or the message.
- Emit raw ANSI from the pure formatter (no `rich`, no `colorama` needed for this):
  DEBUG `\x1b[36m`, INFO `\x1b[32m`, WARNING `\x1b[33m`, ERROR `\x1b[31m`,
  CRITICAL `\x1b[1;31m`, reset `\x1b[0m`.
- Because the decision lives in a pure class, tests assert on the exact escape sequences with no
  terminal involved.
- If color-disabling (`NO_COLOR`, non-TTY) is wanted, it arrives as an **injected flag** on the
  formatter. Never sniff the terminal from inside a pure class.

---

## 12. Checklist for adding a feature

1. Add the `Protocol` in `interfaces/<domain>/<class_name>.py` - one public class per file.
2. Add any new models as frozen Pydantic classes in that same `interfaces/<domain>/` package.
3. Implement it in `modules/<domain>/<impl_name>.py`, with constructor-injected dependencies only.
4. Re-export the new names from both sub-package `__init__.py` files.
5. Register the implementation in `container.py`.
6. Expose the capability as a method on the facade - not in the frontend.
7. Add a thin frontend command that only calls that method.
8. Unit-test the pure class in memory; add a facade integration test using the fakes.
9. Grep that no `print()`, `open()`, or `datetime.now()` crept in outside the edge modules.

---

## 13. When not to use this

The indirection is not free - every capability costs a Protocol, an implementation, a container
entry and a fake. That trade pays off for an application that will grow, get tested, and outlive its
first author. It does not pay off for:

- throwaway scripts and one-off data munging;
- a single-file tool that will never gain a second frontend;
- notebooks and exploratory analysis;
- a thin wrapper around one library, where the wrapper *is* the abstraction.

Applying it to an existing codebase works best incrementally: pull the edges out first (clock,
filesystem, console), since that alone makes most of the code testable, and let `interfaces/` grow
from there.
