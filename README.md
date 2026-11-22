# Official DuckBug SDK for Python

Duck is a developer-focused wrapper for your Python loggers/providers. It provides a unified, flexible interface to handle logging and error monitoring across different providers, with support for multiple log levels and context enrichment.

## 🚀 Quick Start

### Install

```bash
pip install duckbug-sdk
```

### Configuration

Initialize the SDK as early as possible in your application:

```python
from duckbug import Duck, ProviderSetup
from duckbug.providers import DuckBugProvider

Duck.wake([
    ProviderSetup(
        DuckBugProvider.create("__PUBLIC_DSN__"),
        enabled_throwable=True,
        enabled_debug=False,
    )
])
```

### Usage

#### Log exceptions using `quack()`

```python
from duckbug import Duck

try:
    raise Exception("Quack quack")
except Exception as exc:
    Duck.get().quack(exc)
```

#### Log messages with severity levels

```python
from duckbug import Duck

Duck.get().warning("User not found", {"userId": 8})
```

## ⚙️ Custom and Multiple Providers

#### Create your own Provider

```python
from typing import Any, Mapping, Optional

from duckbug import Provider


class MyCustomProvider(Provider):
    def quack(
        self,
        exception: BaseException,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        # Your custom logic for handling exceptions
        pass

    def log(
        self,
        level: Any,
        message: str,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        # Your custom logic for handling logs
        pass
```

#### Initialize Duck with Multiple Providers

```python
from duckbug import Duck, ProviderSetup
from duckbug.providers import DuckBugProvider


Duck.wake([
    ProviderSetup(DuckBugProvider.create("__PUBLIC_DSN__")),
    ProviderSetup(MyCustomProvider()),
])
```

## 🕵️ Pond

Duck also supports gathering request-specific context information via `Pond`.

Python is framework-agnostic, so `Pond` reads context from a per-request `contextvars` storage.
You can set it using the `request_context(...)` helper.

```python
from duckbug import Duck
from duckbug.context import RequestContext, request_context


with request_context(RequestContext(
    ip="192.168.0.1",
    url="https://example.com/test",
    method="POST",
    headers={"Authorization": "Bearer secret"},
    query_params={"q": "duck"},
    body_params={"password": "secret"},
    cookies={"session": "abc123"},
)):
    Duck.get().error("Something went wrong")
```

## 🔌 Integrations

### FastAPI / Starlette (ASGI middleware)

```python
from fastapi import FastAPI

from duckbug.integrations.asgi import DuckBugASGIMiddleware

app = FastAPI()
app.add_middleware(DuckBugASGIMiddleware)
```

### Flask

```python
from flask import Flask

from duckbug.integrations.flask import DuckBugFlask

app = Flask(__name__)
DuckBugFlask(app)
```

### Django

Add middleware to `settings.py`:

```python
MIDDLEWARE = [
    # ...
    "duckbug.integrations.django.DuckBugDjangoMiddleware",
]
```

## 📄 License

Licensed under the MIT license, see [LICENSE](LICENSE).
