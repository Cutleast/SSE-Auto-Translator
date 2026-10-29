### 1\. Scope and Rule Precedence

This document defines the mandatory coding style for Python projects using this guide.

It is based on the Google Python Style Guide, with project-specific conventions taking precedence wherever the two differ.

The rules are applied in the following order:

1.  Rules explicitly defined in this document.
2.  The Google Python Style Guide.
3.  PEP 8 and other standard Python conventions where neither of the above defines a rule.
4.  Existing local project conventions where they do not conflict with this document.

Code should optimize for readability, maintainability, predictable behavior, and static analyzability rather than brevity.

---

### 2\. Language and Runtime

#### 2.1 Python Version

Python 3.12 is the absolute minimum supported version.

New projects should target Python 3.14 or newer.

Existing projects should target the newest Python version supported by their runtime environment unless project-specific compatibility requirements prevent it.

Code may use language and typing features available in the project's configured Python version without providing compatibility fallbacks for older versions than the declared minimum.

#### 2.2 Language

All source-code-related text must be written in English. This includes:

*   identifiers
*   comments
*   docstrings
*   log messages
*   exception messages
*   developer-facing diagnostic messages

User-facing application text may be subject to localization requirements and is not covered by this rule.

---

### 3\. Formatting

#### 3.1 Line Length

The maximum line length is 90 characters.

This limit applies to:

*   source code
*   comments
*   docstrings
*   type annotations
*   string literals

Long expressions should preferably be split using implicit continuation inside parentheses, brackets, or braces.

Use a backslash for explicit line continuation only when no reasonable implicit continuation is possible.

Break expressions as soon as they would exceed the line limit.

```python
result: Result = service.process(request=request, options=options)

result: Result = service.process(request=request, options=options, payload=payload)

result: Result = service.process(
    request=request, options=options, payload=payload, headers=headers
)

result: Result = service.process(
    request=request,
    options=options,
    payload=payload,
    headers=headers,
    validator=validator,
)
```

Do not split unless necessary to stay within the line limit.

Do not split expressions in ways that obscure their structure.

#### 3.2 Indentation

Use four spaces per indentation level.

Tabs must not be used for indentation.

For continued expressions, use either:

*   alignment with an opening delimiter or
*   a four-space hanging indent.

When each item or argument occupies its own line, use a trailing comma and place the closing delimiter on its own line.

```python
values: list[Value] = [
    first_value,
    second_value,
    third_value,
]
```

#### 3.3 Blank Lines

Use two blank lines between top-level class and function definitions.

Use one blank line between methods.

Single blank lines may be used inside functions to separate logical sections.

Exactly one blank line must follow every docstring before the first statement, decorator, or other code belonging to that documented object.

In general, separate completed logical blocks from the following unrelated statement with a blank line where this improves readability.

```python
def calculate(value: int) -> int:
    """
    Calculates the resulting value.

    Args:
        value (int): Input value.

    Returns:
        int: Calculated value.
    """

    return value * 2
```

#### 3.4 Whitespace

Follow standard Python whitespace conventions.

Do not place whitespace:

*   immediately inside parentheses, brackets, or braces
*   before commas, semicolons, or colons
*   before an opening parenthesis used for a function call
*   before an opening bracket used for indexing

Use one space around assignment, comparison, and Boolean operators.

Do not vertically align assignments or other tokens by inserting extra whitespace.

```python
short_name: int = 1
longer_name: int = 2
```

Do not write:

```python
short_name: int = 1
longer_name: int = 2
```

#### 3.5 Statements

Use one statement per line.

Do not compress control-flow statements into a single line merely because they fit.

Prefer:

```python
if condition:
    perform_action()
```

over:

```python
if condition:
    perform_action()
```

#### 3.6 Semicolons

Do not terminate statements with semicolons.

Do not use semicolons to place multiple statements on one line.

---

### 4\. File Structure

#### 4.1 File Header

Unless the project defines a different header convention, every Python file must begin with the following module docstring:

```python
"""
Copyright (c) Cutleast
"""
```

#### 4.2 Module Organization

A module should generally contain one primary class.

Each class should have its own module unless a smaller internal class strictly belongs to another class and has no meaningful independent use.

Such implementation-specific classes may be nested inside the owning class.

Top-level functions should be kept focused and placed in modules that clearly represent their purpose.

#### 4.3 Executable Modules

Executable modules must keep executable behavior behind a `main()` function and a standard module guard.

```python
def main() -> None:
    """
    Runs the application.
    """

    ...


if __name__ == "__main__":
    main()
```

Importing a module must not unintentionally execute application logic.

---

### 5\. Imports

#### 5.1 General Rules

Imports belong at the top of the module, after the file header and before module-level declarations.

Do not use wildcard imports.

```python
from package import *
```

is prohibited.

Prefer explicit imports whose origin is immediately identifiable.

#### 5.2 Import Groups

Group imports in this order:

1.  standard-library imports
2.  third-party imports
3.  project imports

Separate groups with one blank line.

Imports within each group should be sorted alphabetically.

#### 5.3 Relative and Absolute Imports

Use relative imports within the same package or for subpackages.

```python
from .models import User
from .utilities.formatter import Formatter
from common.logger import (
    Logger,
)  # "common" is a root package outside of the current package
```

Use absolute imports when importing from outside the current package.

This rule overrides the Google Python Style Guide's general preference for absolute imports.

#### 5.4 Typing Imports

Import typing symbols directly from `typing`.

```python
from typing import ClassVar, Optional, Self, cast, final, override
```

Do not use `typing_extensions` for features available in the project's configured Python version.

Prefer built-in collection generics:

```python
list[str]
dict[str, int]
tuple[int, ...]
```

instead of legacy forms such as:

```python
List[str]
Dict[str, int]
Tuple[int, ...]
```

---

### 6\. Type Annotations

#### 6.1 General Requirement

Code must be fully typed.

Provide type annotations for:

*   every function parameter
*   every function return value
*   every class attribute
*   every local variable unless the assignment ends in a constructor call or a cast
    *   Loop targets, comprehension targets, exception targets, and similar language-bound variables are exempt.

```python
example: int = 42
example_text: str = "example"

my_object = MyClass()  # no annotation required
another_object: MyClass = (
    MyClass.create()
)  # annotation required, because of the method call
casted_object = cast(MyClass, unknown_object)  # no annotation, because of the cast
```

`self` and `cls` do not require annotations.

```python
def parse_file(path: Path) -> ParsedFile: ...
```

Constructors must explicitly declare `-> None`.

```python
def __init__(self) -> None: ...
```

#### 6.2 Union Types

Use modern `|` syntax for unions.

```python
value: str | int
```

For optional values, however, always use `Optional[T]`.

```python
value: Optional[str]
```

Do not use:

```python
value: str | None
```

This project-specific rule overrides the preferred modern optional syntax in the Google Python Style Guide.

#### 6.3 Collection Types

Prefer concrete built-in collection annotations where the concrete type is part of the contract.

```python
items: list[str]
mapping: dict[str, int]
```

Use abstract collection interfaces where callers do not need to provide a specific concrete implementation.

```python
from collections.abc import Iterable, Sequence
```

#### 6.4 `Any`

Avoid `Any` when a more precise type can reasonably be expressed.

Use `Any` only where the underlying interface genuinely cannot be represented more precisely or where an external untyped API requires it.

Do not use `Any` merely to silence a type-checking error.

#### 6.5 Type Narrowing

Use explicit type narrowing where necessary.

Use `cast()` when the type checker cannot infer a type that is already known by the program's logic.

```python
widget = cast(CustomWidget, item.widget())
```

Do not use `cast()` to conceal an actual type incompatibility.

#### 6.6 Forward References

Prefer approaches supported by the configured Python version that preserve static type checking.

Use `from __future__ import annotations` when it meaningfully simplifies forward references or circular annotation dependencies and remains applicable to the configured Python version.

#### 6.7 Type Aliases

Use type aliases for complex types when they improve readability.

Names of public type aliases use `PascalCase`.

Private module-local aliases begin with an underscore.

---

### 7\. Naming

#### 7.1 General Naming Conventions

Use descriptive names.

Avoid abbreviations unless they are standard and unambiguous in the relevant domain.

Do not shorten words merely to reduce identifier length.

Use:

| Element | Convention |
| --- | --- |
| Packages | `lower_snake_case` |
| Modules | `lower_snake_case` |
| Classes | `PascalCase` |
| Exceptions | `PascalCase` ending in `Error` |
| Functions | `lower_snake_case` |
| Methods | `lower_snake_case` |
| Parameters | `lower_snake_case` |
| Local variables | `lower_snake_case` |
| Public attributes | `lower_snake_case` |
| Constants | `UPPER_SNAKE_CASE` |

Python filenames must end in `.py` and must not contain hyphens.

#### 7.2 Private Attributes

Private instance and class attributes use double-underscore name mangling.

```python
class Service:
    __client: Client
    __running: bool
```

Private methods follow the same convention where they are implementation details of the class.

```python
def __load_config(self) -> None: ...
```

This rule intentionally differs from the Google Python Style Guide, which generally prefers a single leading underscore.

#### 7.3 Protected Attributes

Attributes and methods intended for use by subclasses use a single leading underscore.

```python
class BaseService:
    _state: State

    def _reset_state(self) -> None: ...
```

#### 7.4 Instance Member Attributes

Declare class-level attribute annotations near the top of the class body.

Do not assign a value to instance-member declarations at class level. Values must be assigned per instance, normally in **init**, to clearly distinguish instance state from class state. Constants are exempt from this rule.

```python
class Service:
    __client: Client
    __state: State
```

#### 7.5 Constants

Class and module constants use `UPPER_SNAKE_CASE` and must be annotated.

```python
DEFAULT_PORT: int = 1234
```

#### 7.6 Single-Character Names

Avoid single-character names except where their meaning is conventional and their scope is very small, such as:

*   simple loop counters
*   established mathematical notation
*   narrowly scoped comprehensions.

Prefer descriptive names whenever they improve clarity.

---

### 8\. Strings

#### 8.1 Formatting

Prefer f-strings for string interpolation.

```python
message: str = f"Loaded '{file_name}'."
```

Do not use `%` formatting for ordinary string construction.

Use `.format()` only when it offers a concrete advantage over an f-string.

#### 8.2 Object Values in Messages

When object or value representations are embedded in log or diagnostic messages, surround them with single quotes where this improves boundaries and readability.

```python
self.log.debug(f"Loaded profile '{profile_name}'.")
```

#### 8.3 String Concatenation

Prefer implicit concatenation for static strings split across lines.

Use runtime concatenation only when it is semantically necessary.

```python
message: str = (
    "This is an extremely, extraordinarily long message that has been split across "
    "multiple source lines."
)
```

Follow these points, when breaking long strings:

*   Always break following a whitespace or a newline character (`\n`).
*   Prefer the latest natural breaking point that does not exceed the line limit.

---

### 9\. Docstrings

#### 9.1 General Requirement

Every module, class, non-overriding method, function and public/protected field must have a docstring.

This includes:

*   private functions
*   private methods
*   constructors with parameters in addition to `self` or notable exceptions
*   test classes
*   test methods

Methods overriding a base-class method do not require a docstring unless the override introduces behavior, constraints, parameters, return semantics, or exceptions that are not sufficiently documented by the inherited method.

Always use triple double-quotes for docstrings.

Use multi-line docstrings for classes, functions and methods (or callables in general):

```python
"""
Documentation.
"""
```

Use single-line docstrings for fields and properties:

```python
"""Documentation."""
```

#### 9.2 Summary

Start ordinary class, function, and method docstrings with a concise summary describing the documented object's purpose or behavior.

Prefer descriptions of what an object represents or what a function does.

```python
class UserRepository:
    """
    Provides persistent access to user data.
    """
```

Avoid redundant wording such as:

```python
class UserRepository:
    """
    Class representing a user repository.
    """
```

Constructors are an exception to this rule. Their purpose is already implied by `__init__`, so they must not contain redundant summaries such as `"Initializes the service."`.

#### 9.3 Function and Method Documentation

Ordinary functions and methods use Google-style sections.

```python
def add(a: int, b: int) -> int:
    """
    Calculates the sum of two integers.

    Args:
        a (int): First integer.
        b (int): Second integer.

    Returns:
        int: Sum of both integers.
    """

    return a + b
```

Parameter and return types must be included in the corresponding documentation even when they are already available through type annotations.

#### 9.4 Constructor Documentation

Constructors must not contain a summary merely stating that an object is initialized.

Document only:

*   constructor parameters under `Args:`
*   raised exceptions under `Raises:`, where applicable

```python
def __init__(self, client: Client) -> None:
    """
    Args:
        client (Client): Client used by the service.
    """

    self.__client = client
```

A constructor without parameters other than `self` and without notable raised exceptions may use a minimal empty-purpose docstring only if required by tooling or project configuration. Otherwise, no redundant descriptive text should be added solely to satisfy documentation requirements.

#### 9.5 Section Requirements

Use the following sections where applicable:

*   `Args:`
*   `Returns:`
*   `Yields:`
*   `Raises:`

For ordinary functions and methods, `Args`, `Returns`, and `Raises` may all be omitted only when the function:

*   accepts no arguments other than `self` or `cls`
*   returns `None` and
*   raises no notable exceptions

Document every exception explicitly raised by the documented function under `Raises:`.

```python
Raises:
    ValueError: The supplied identifier is invalid.
```

For generators, use `Yields:` instead of `Returns:` to document yielded values.

#### 9.6 Blank Lines After Docstrings

Exactly one blank line must immediately appear after every (multi-line and single-line) docstring.

```python
def calculate(value: int) -> int:
    """
    Calculates a value.

    Args:
        value (int): Input value.

    Returns:
        int: Calculated value.
    """

    return value * 2
```

#### 9.7 Overridden Methods

Methods overriding a base-class method do not require a docstring when the inherited documentation remains accurate.

The `@override` decorator must still be present.

```python
@override
def showEvent(self, event: QShowEvent) -> None:
    super().showEvent(event)
```

Add a docstring only when the override introduces relevant behavior or semantics that are not sufficiently described by the base method.

Do not duplicate inherited documentation merely for completeness.

#### 9.8 Properties and Public Fields

Properties follow the same documentation convention as public fields.

Use a concise single-line docstring whenever it fits within the maximum line length.

```python
@property
def current_user(self) -> User:
    """The currently authenticated user."""

    return self.__current_user
```

If the documentation would exceed the maximum line length, use a simple multi-line docstring without additional `Returns:` or similar sections.

```python
@property
def current_user(self) -> User:
    """
    The currently authenticated user including all resolved account metadata.
    """

    return self.__current_user
```

Do not add `Args:`, `Returns:`, or other structured sections to a property unless exceptional behavior genuinely requires additional documentation.

Public fields follow the same principle:

```python
name: str
"""The displayed user name."""
```

If the documentation exceeds the maximum line length:

```python
description: str
"""
An extremely long description of the field that cannot reasonably fit into a single
source line.
"""
```

#### 9.9 Comments

Comments should explain intent, reasoning, constraints, or non-obvious behavior.

Do not write comments that merely restate the code.

Prefer:

```python
# Keep the handle alive because Qt stores only a weak native reference.
self.__window_handle = handle
```

over:

```python
# Assign handle to window handle.
self.__window_handle = handle
```

Comments should use normal capitalization, spelling, and punctuation.

Do not use decorative section separators such as:

```python
# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #
```

---

### 10\. Classes

#### 10.1 Responsibilities

Classes should have a clear responsibility.

Avoid classes that combine unrelated concerns merely because those concerns are used by the same feature.

#### 10.2 Initialization

Declare instance-member types at class level.

```python
class Service:
    """
    An example service class.
    """

    __client: Client
    __running: bool

    def __init__(self, client: Client) -> None:
        """
        Args:
            client (Client): Client used by the service.
        """

        self.__client = client
        self.__running = False
```

#### 10.3 Properties and Accessors

Do not create getters and setters solely to wrap trivial attribute access unless encapsulation is required by the class design.

Use properties for inexpensive, unsurprising attribute-like behavior.

Properties use the same concise documentation style as public fields.

Use explicit methods when an operation:

*   performs significant work
*   has notable side effects
*   invalidates or rebuilds state
*   can fail in a meaningful way

#### 10.4 Small Functions and Methods

Prefer small, focused functions and methods.

A function exceeding approximately 40 lines should prompt consideration of whether it can be decomposed without harming readability or cohesion.

This is a review guideline, not a hard limit.

#### 10.5 Static and Class Methods

Make a method static, if it provides a small utilitarian functionality that does not depend on the state of an instance and is not designed to be overridden or changed by subclasses.

Turn a method into a class method, if it provides a stateless functionality that is specific to the type of the class and/or designed to be overridden or changed by subclasses.

To further solidify this distinction, static methods should be called on the class that they are defined in instead of `self`:

```python
MyClass.my_static_method(...)
```

instead of:

```python
self.my_static_method(...)
```

For class methods though - since they are dependent on the type of the class, call them either on `self` or on `self.__class__`:

```python
self.my_class_method(...)
```

This also applies to private and protected methods, respectively.

#### 10.6 Class Constants

Constants declared on a class level must be referenced like static methods (see previous section):

```python
MyClass.MY_CONST
```

instead of:

```python
self.MY_CONST
```

This also applies to private and protected constants, respectively.

---

### 11\. Control Flow and Expressions

#### 11.1 Boolean Evaluation

Use Python's natural truth-value testing where appropriate.

```python
if items:
    ...
```

instead of:

```python
if len(items) > 0:
    ...
```

Use explicit `is None` and `is not None` checks for optional values.

```python
if value is None:
    ...
```

Do not use truth-value testing when `None` must be distinguished from another false value such as `0`, `False`, or an empty collection.

#### 11.2 Conditional Expressions

Conditional expressions are suitable for simple cases.

```python
label: str = enabled_text if enabled else disabled_text
```

Use a regular `if` statement when either expression or the condition becomes complex.

#### 11.3 Comprehensions

Use comprehensions for simple transformations and filtering.

```python
names: list[str] = [user.name for user in users if user.enabled]
```

Avoid comprehensions containing multiple nested loops or several independent conditions when an explicit loop is easier to understand.

#### 11.4 Lambdas

Use lambdas only for short and simple expressions.

Prefer named functions when logic becomes non-trivial or when a descriptive function name improves readability.

#### 11.5 Iteration

Use Python's standard iteration protocol.

```python
for item in items:
    ...
```

Do not create unnecessary intermediate lists.

Prefer:

```python
for key in mapping:
    ...
```

over:

```python
for key in mapping.keys():
    ...
```

when only keys are needed.

---

### 12\. Exceptions

#### 12.1 Exception Types

Use built-in exception classes when they accurately describe the failure.

Examples include:

*   `ValueError` for invalid values
*   `TypeError` for inappropriate types
*   `KeyError` for missing mapping keys
*   `RuntimeError` for runtime state errors where no more specific type exists

Custom exception types should inherit from an appropriate existing exception class and normally end in `Error`.

#### 12.2 Assertions

Do not use `assert` for:

*   input validation
*   runtime error handling
*   conditions required for correct application behavior

Assertions may be used for internal invariants whose removal does not alter required behavior.

Assertions are expected in pytest tests.

#### 12.3 Exception Handling

Catch the narrowest appropriate exception type.

Avoid:

```python
except:
    ...
```

Catching `Exception` is acceptable only at intentional isolation boundaries, such as:

*   worker-thread entry points
*   task dispatch boundaries
*   top-level error reporting
*   code that records and deliberately suppresses otherwise unhandled failures

Keep `try` blocks as small as practical.

Do not silently suppress exceptions without a documented reason.

#### 12.4 Cleanup

Use `finally` when cleanup must occur regardless of whether an exception was raised.

Prefer context managers for resources supporting deterministic cleanup.

---

### 13\. Resources and Paths

#### 13.1 Filesystem Paths

Always use `pathlib.Path` for filesystem paths.

```python
from pathlib import Path

config_path: Path = Path("config") / "settings.json"
```

Do not represent application filesystem paths as manually manipulated raw strings unless required by an external API.

Convert a `Path` to `str` only at the API boundary where necessary.

#### 13.2 Resource Management

Use `with` statements for resources such as files whenever possible.

```python
with file_path.open("r", encoding="utf-8") as file:
    content: str = file.read()
```

If just a file is read without any other operations, though, this is also sufficient:

```python
content: str = file_path.read_text("utf-8")
```

Do not rely on garbage collection or destructors for observable resource cleanup.

---

### 14\. Logging

#### 14.1 Logger Definition

Define a logger as a class attribute using the class name.

```python
class Service:
    log: logging.Logger = logging.getLogger("Service")
```

#### 14.2 Message Formatting

Prefer f-strings.

```python
self.log.debug(f"Loading file '{path}'.")
```

Values embedded into messages should generally be delimited with single quotes when appropriate.

#### 14.3 Exceptions

Use `exc_info` when traceback information is relevant.

Do not duplicate information unnecessarily between a log message and an exception traceback.

Select log levels according to semantic importance rather than expected message frequency.

---

### 15\. Mutable State and Defaults

#### 15.1 Global State

Avoid mutable global state.

Module-level constants are acceptable.

State shared across components should generally be owned by an explicit object or service.

#### 15.2 Mutable Default Arguments

Never use mutable objects as function defaults.

Do not write:

```python
def process(items: list[str] = []) -> None: ...
```

Use an optional value and create the collection inside the function instead.

```python
def process(items: Optional[list[str]] = None) -> None:
    """
    Processes the specified items.

    Args:
        items (Optional[list[str]], optional): Items to process. Defaults to None.
    """

    if items is None:
        items = []
```

---

### 16\. PySide6 and Qt (if applicable to the current project)

#### 16.1 Framework and Version

All Qt code uses PySide6.

PySide6 6.10 is the absolute minimum supported version.

New projects should target the latest stable PySide6 version.

Existing projects should use the PySide6 version configured by the project and should normally be upgraded to current stable releases unless compatibility requirements prevent it.

Do not use PyQt5 or PyQt6 APIs, imports, conventions, or compatibility layers.

Do not deliberately restrict an implementation to PySide6 6.10 APIs when the configured project version provides a newer and more appropriate API.

#### 16.2 Signals

Every `Signal` must have a docstring directly below its declaration.

```python
class ServiceHandler(QObject):
    """
    Handles service operations.
    """

    handled = Signal(Service)
    """
    Signal emitted when a service was handled.

    Args:
        Service: Service that was handled.
    """
```

#### 16.3 Overrides

Use `@override` from `typing` on every method overriding a base-class method.

Overridden Qt methods do not require a docstring unless they alter the inherited behavior.

```python
from typing import override


class Widget(QWidget):
    @override
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
```

#### 16.4 QObject-Based Components

Prefer `QObject`\-based classes for components requiring Qt signals or Qt translations.

Do not reproduce signal-like observer behavior manually when Qt signals provide the intended semantics.

#### 16.5 Singleton QObjects

Singleton classes derived from `QObject` must inherit from `SingletonQObject` when that project infrastructure is available.

Use the provided singleton API instead of implementing a second singleton mechanism.

#### 16.6 User Interface Initialization

UI initialization must be delegated to private helper methods.

```python
class MainWindow(QMainWindow):
    """
    The main window of the application.
    """

    @override
    def __init__(self) -> None:
        self.__init_ui()

        self.__button.clicked.connect(self.__on_button_clicked)

    def __init_ui(self) -> None:
        """
        Initializes the user interface.
        """

        ...
```

Signal connections are established in `__init__` after `__init_ui()` returns unless a more specific lifecycle requirement makes that impossible.

Larger UI sections may use additional initialization methods such as:

```python
self.__init_menu_bar()
self.__init_toolbar()
self.__init_content()
```

#### 16.7 Translatable Text

Wrap user-visible Qt strings in `self.tr(...)`.

```python
self.__button.setText(self.tr("Open file"))
```

Do not apply translation wrapping to:

*   internal identifiers
*   log messages
*   file formats
*   protocol values
*   developer-facing diagnostic strings

---

### 17\. Data Models

#### 17.1 Pydantic

Pure data classes and data models must derive from `pydantic.BaseModel`.

Do not use `@dataclass` for these models.

```python
from pydantic import BaseModel


class UserData(BaseModel):
    """
    Represents persisted user data.
    """

    name: str
    """The user's name."""
```

#### 17.2 Field Documentation

Every public model field must have a docstring directly below its declaration.

Use a single-line docstring whenever the field description fits within the maximum line length.

```python
class UserData(BaseModel):
    """
    Represents user data.
    """

    last_installed_version: str
    """The version of the mod list when the application was last started."""

    game_language: Language
    """The selected language for the game."""
```

If the description would exceed the maximum line length, use a simple multi-line docstring.

```python
description: str
"""
An extremely long description of the field that cannot reasonably fit into a single
source line.
"""
```

Do not add structured sections to field docstrings.

#### 17.3 Immutable Models

Use `frozen=True` for models whose instances are conceptually immutable.

The model configuration should represent the semantic contract of the model, not merely prevent accidental mutation in selected call sites.

```python
class UserData(BaseModel, frozen=True): ...
```

#### 17.4 Assignment Validation

When mutable model instances require validation after construction, use:

```python
class UserData(BaseModel, validate_assignments=True): ...
```

#### 17.5 Serialization

When JSON serialization follows the standard project convention, use:

```python
model.model_dump_json(indent=4, by_alias=True, exclude_defaults=True)
```

Deviate only when the serialization format explicitly requires different behavior or if the serialized output is purely for internal purposes and only read by machines.

---

### 18\. Project Structure

#### 18.1 Source Layout

Production source code resides under `src/`.

Package structure mirrors the directory hierarchy.

For example:

```
src/core/nxm/handler.py
```

contains:

```
core.nxm.handler.NxmHandler
```

#### 18.2 One Primary Class per Module

Place each primary class in its own module.

A module filename should represent the contained class using `lower_snake_case`.

Example:

```
progress_executor.py
```

for:

```python
class ProgressExecutor: ...
```

#### 18.3 Package Management

Use `uv` as the package manager and build-tool foundation.

For monorepos, use `[tool.uv.workspace]` for workspace members.

#### 18.4 Static Analysis

Use Pyright in strict mode.

Code must satisfy the applicable Pyright configuration from `pyproject.toml`.

Do not weaken type safety globally to work around an isolated issue.

Use narrowly scoped suppressions only when the type system cannot correctly represent valid code, and document the reason when it is not obvious.

#### 18.5 Linting and Formatting

Use Ruff for linting and formatting according to the project's `pyproject.toml`.

Project configuration takes precedence over Ruff defaults.

Do not manually introduce formatting that will immediately be normalized by the configured formatter.

---

### 19\. Testing

#### 19.1 Framework

Use pytest.

The standard test environment may include:

*   `pytest`
*   `pytest-mock`
*   `pytest-qt`
*   `pytest-cov`
*   `pyfakefs`

#### 19.2 Test Layout

Tests mirror the production source structure under `tests/`.

Example:

```
src/core/utilities/logger.py
tests/core/utilities/test_logger.py
```

For:

```python
core.utilities.logger.Logger
```

use:

```python
class TestLogger: ...
```

#### 19.3 Test Classes

Group tests by the production class being tested.

```python
class TestLogger:
    """
    Tests `core.utilities.logger.Logger`.
    """

    def test_something(self) -> None:
        """
        Tests that the expected behavior occurs.
        """

        # given
        ...  # setup here

        # when
        ...  # run the tested functionality

        # then
        assert ...  # check the output
```

#### 19.4 Given / When / Then

Structure test bodies using:

```python
# given
```

```python
# when
```

```python
# then
```

Sections may be omitted when genuinely inapplicable, but tests should preserve a clear distinction between setup, action, and verification.

#### 19.5 Assertions

Use normal pytest `assert` statements.

Prefer precise assertions that identify the relevant behavior.

Do not hide essential assertions inside general-purpose helper functions unless the helper itself represents a meaningful reusable assertion.

#### 19.6 Shared Test Infrastructure (if applicable to the current project)

Inherit from:

```python
cutleast_core_lib.test.base_test.BaseTest
```

when shared fixtures or helper infrastructure from the core library is needed.

Do not inherit from it without using the functionality it provides.

#### 19.7 Standard Pytest Configuration

The standard configuration contains:

```
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "tests"]
log_cli = true
log_cli_level = "DEBUG"
addopts = "-vv"
```

Project-specific additions may extend these values.

---

### 20\. TODO Comments

Use TODO comments only for temporary or deliberately incomplete code.

Prefer referencing a tracked issue or other durable context.

```python
# TODO: #123 - Replace the compatibility implementation.
```

A TODO should make clear:

*   what remains to be done
*   why it has not yet been done
*   where additional context is tracked

Do not use a person's name as the sole context for a TODO.

---

### 21\. Design and Readability

#### 21.1 Readability over Concision

Prefer clear code over shorter code.

Do not use a clever expression when a slightly longer implementation makes intent easier to understand.

#### 21.2 Explicit Behavior

Public APIs should make non-trivial behavior visible.

Do not conceal expensive work, I/O, state rebuilding, or major side effects behind an interface that appears to be trivial attribute access.

#### 21.3 Encapsulation

Keep implementation details private or protected according to their intended scope.

Do not expose internal state merely to make testing easier.

Tests may exercise protected behavior where appropriate, but implementation details should not become public API solely for test access.

#### 21.4 Avoid Premature Abstraction

Create abstractions when they represent a stable concept or eliminate meaningful duplication.

Do not create wrappers, base classes, factories, or generic helpers solely in anticipation of possible future reuse, unless future reuse is already explicitely planned.

#### 21.5 Consistency

When several implementations are equally readable and correct, prefer the one already established in the surrounding project.

Consistency is not a justification for preserving code that directly violates this guide.

---

### 22\. Mandatory Review Checklist

Before considering Python code complete, verify all of the following:

1.  Every `.py` file uses the project-defined file header. If the project does not define a custom header convention, use the default copyright module docstring.
2.  All source-code-related text is written in English, including identifiers, comments, docstrings, log messages, exception messages, and developer-facing diagnostics.
3.  The configured Python version is at least Python 3.12. New projects target Python 3.14 or newer unless compatibility requirements prevent it.
4.  Every function parameter and return value is fully type-annotated.
5.  Every class attribute and instance-member declaration is type-annotated.
6.  Explicitly assigned local variables are type-annotated unless the assignment directly uses a constructor call or `cast()`.
7.  Loop targets, comprehension targets, exception targets, and similar language-bound variables are not required to have explicit annotations.
8.  `Optional[T]` is used for nullable values instead of `T | None`.
9.  Built-in generic types such as `list[str]` and `dict[str, int]` are used instead of legacy `typing` collection aliases.
10.  `typing_extensions` is not used for features already available in the configured Python version.
11.  No source-code line exceeds 90 characters.
12.  Long expressions are split only when necessary and are not broken in ways that obscure their structure.
13.  Multi-line argument or item lists use a trailing comma when each argument or item occupies its own line.
14.  Required modules, classes, functions, and non-overriding methods have docstrings.
15.  Constructors with parameters other than `self`, or constructors with notable exceptions, have docstrings.
16.  Constructor docstrings contain only `Args:` and, where applicable, `Raises:` sections and do not contain redundant initialization summaries.
17.  Parameterless constructors without notable exceptions do not contain artificial documentation solely to satisfy a docstring requirement.
18.  Overridden methods do not duplicate inherited documentation when the inherited documentation remains accurate.
19.  Overridden methods that introduce relevant new behavior, constraints, parameters, return semantics, or exceptions document those differences.
20.  Every overriding method uses `@override`.
21.  Properties use the same concise documentation style as public fields.
22.  Property and field docstrings use a single-line form when they fit within the maximum line length.
23.  Property and field docstrings use a simple multi-line form when the documentation does not reasonably fit on one line.
24.  Property and field docstrings do not contain structured sections unless exceptional behavior requires additional documentation.
25.  Public and protected fields that require documentation have a docstring directly associated with their declaration.
26.  Exactly one blank line follows every docstring before the next statement or declaration.
27.  Every explicitly raised exception that forms part of the documented behavior is documented under `Raises:`.
28.  Private members use double-underscore name mangling.
29.  Protected members use a single leading underscore.
30.  Instance-member declarations are placed near the top of the class body.
31.  Instance-member declarations at class level do not assign per-instance values.
32.  Class and module constants use annotated `UPPER_SNAKE_CASE`.
33.  Wildcard imports are not used.
34.  Imports are grouped into standard-library, third-party, and project imports, with groups separated by one blank line.
35.  Imports are sorted alphabetically within their group.
36.  Relative imports are used within the same package and its subpackages.
37.  Absolute imports are used when importing from outside the current package.
38.  Filesystem paths use `pathlib.Path` unless an external API explicitly requires another representation.
39.  Resources with deterministic lifetime requirements use context managers or another explicit cleanup mechanism.
40.  Mutable default arguments are not used.
41.  Mutable global state is avoided unless it represents intentional shared application state.
42.  Exceptions are caught as narrowly as practical.
43.  Bare `except:` clauses are not used.
44.  Broad `Exception` handling is limited to deliberate isolation boundaries.
45.  Comments explain intent, constraints, reasoning, or non-obvious behavior rather than restating the implementation.
46.  Decorative comment separators are not used.
47.  Each primary class has its own module.
48.  Smaller implementation-specific classes are nested only when they have no meaningful independent use.
49.  PySide6 is used for all Qt code.
50.  The configured PySide6 version is at least 6.10.
51.  New Qt projects target the latest stable PySide6 version unless compatibility requirements prevent it.
52.  Existing Qt projects use the version configured by the project and are not unnecessarily restricted to PySide6 6.10 APIs when newer configured APIs are available.
53.  PyQt5, PyQt6, and related compatibility conventions are not used.
54.  Qt imports follow the order `QtCore`, `QtGui`, `QtWidgets`.
55.  Every Qt `Signal` has a docstring directly below its declaration.
56.  Qt overrides follow the same documentation rules as other overridden methods.
57.  User-visible Qt strings are wrapped in `self.tr(...)`.
58.  UI initialization is delegated to private initialization helpers.
59.  Signal connections are normally established in `__init__` after `__init_ui()` returns.
60.  Pure data classes and data models derive from `pydantic.BaseModel`.
61.  `@dataclass` is not used for pure data models.
62.  Every public Pydantic model field has a field-style docstring.
63.  Immutable Pydantic models use `frozen=True` when immutability is part of the model's semantic contract.
64.  Mutable Pydantic models enable assignment validation when live validation after construction is required.
65.  Standard model JSON serialization uses the documented `model_dump_json(...)` convention unless the target format requires different behavior.
66.  Pyright passes in strict mode under the project's configuration.
67.  Ruff passes under the project's configured linting and formatting rules.
68.  Production code resides under `src/` unless the project defines a different source layout.
69.  Tests mirror the production source structure under `tests/`.
70.  Tests are grouped in classes corresponding to the production class being tested.
71.  Test bodies use `# given`, `# when`, and `# then` where those phases are applicable.
72.  Tests use normal pytest `assert` statements.
73.  Shared test infrastructure is inherited only when its fixtures or helpers are actually needed.
74.  Functions and methods remain focused and reasonably sized.
75.  Public APIs do not hide substantial work, I/O, state rebuilding, or major side effects behind interfaces that appear trivial.
76.  New abstractions represent an actual stable concept, meaningful duplication, or explicitly planned reuse.
77.  The final implementation favors readability, maintainability, predictable behavior, and static analyzability over unnecessary concision.