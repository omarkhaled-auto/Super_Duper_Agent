# Build 3 Technology Research: Testing Technologies

> Verified against official documentation as of 2026-02-14.
> Sources: Schemathesis readthedocs (stable), Pact Python v3.2.1 API docs, Testcontainers Python (GitHub + readthedocs), httpx (encode/httpx), pytest-asyncio docs.

---

## 1. Schemathesis (Latest Stable — v4.x)

### 1.1 Installation

```bash
pip install schemathesis
# CLI alias: st (or uvx schemathesis)
```

### 1.2 Schema Loaders — Python API

All loaders are under `schemathesis.openapi.*` (OpenAPI) and `schemathesis.graphql.*` (GraphQL).

```python
import schemathesis

# --- OpenAPI Loaders ---

# From URL (most common for live services)
schema = schemathesis.openapi.from_url(
    url: str,                              # Full URL to OpenAPI schema
    *,
    config: SchemathesisConfig | None = None,
    wait_for_schema: float | None = None,  # Max seconds to wait for availability
    **kwargs: Any,                         # Passed to requests.get() (headers, timeout, auth)
)

# From filesystem path
schema = schemathesis.openapi.from_path(
    path: PathLike | str,                  # JSON or YAML file
    *,
    config: SchemathesisConfig | None = None,
    encoding: str = 'utf-8',
)

# From file-like object or string
schema = schemathesis.openapi.from_file(
    file: IO[str] | str,
    *,
    config: SchemathesisConfig | None = None,
)

# From ASGI app (FastAPI, Starlette)
schema = schemathesis.openapi.from_asgi(
    path: str,    # e.g., "/openapi.json"
    app: Any,     # ASGI app instance
    *,
    config: SchemathesisConfig | None = None,
    **kwargs: Any,
)

# From WSGI app (Flask)
schema = schemathesis.openapi.from_wsgi(
    path: str,
    app: Any,
    *,
    config: SchemathesisConfig | None = None,
    **kwargs: Any,
)

# From dictionary
schema = schemathesis.openapi.from_dict(
    schema: dict[str, Any],
    *,
    config: SchemathesisConfig | None = None,
)

# From pytest fixture (lazy loading)
schema = schemathesis.pytest.from_fixture(name: str)
```

### 1.3 Test Generation — @schema.parametrize()

The `parametrize()` decorator generates pytest test cases for each API operation in the schema.

```python
import schemathesis

schema = schemathesis.openapi.from_url("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_api(case):
    """Each API operation gets its own test case with generated data."""
    case.call_and_validate()
```

### 1.4 Case Object — Core Data Structure

```python
# Case is a dataclass with:
case.method: str              # HTTP verb (GET, POST, etc.)
case.path: str                # Path template (e.g., /users/{user_id})
case.formatted_path: str      # Path with variables substituted
case.body: Any                # Generated request body
case.headers: dict | None     # Generated HTTP headers
case.cookies: dict | None     # Generated cookies
case.query: dict | None       # Generated query parameters
case.path_parameters: dict    # Generated path variables
case.media_type: str | None   # Media type from schema
case.id: str                  # Random ID for log correlation
```

### 1.5 Case Methods

```python
# Make request WITHOUT validation (manual validation)
response = case.call(
    base_url: str | None = None,
    session: requests.Session | None = None,
    headers: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    cookies: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Response

# Make request WITH automatic validation (primary usage)
response = case.call_and_validate(
    base_url: str | None = None,
    session: requests.Session | None = None,
    headers: dict[str, Any] | None = None,
    checks: list[CheckFunction] | None = None,          # Override all checks
    additional_checks: list[CheckFunction] | None = None, # Add custom checks
    excluded_checks: list[CheckFunction] | None = None,   # Skip specific checks
    **kwargs: Any,
) -> Response

# Validate an existing response
case.validate_response(
    response: Response,                                    # requests/httpx/werkzeug Response
    checks: list[CheckFunction] | None = None,
    additional_checks: list[CheckFunction] | None = None,
    excluded_checks: list[CheckFunction] | None = None,
    headers: dict[str, Any] | None = None,
    transport_kwargs: dict[str, Any] | None = None,
)

# Generate curl command for reproduction
curl_cmd: str = case.as_curl_command(
    headers: Mapping[str, Any] | None = None,
    verify: bool = True,
)
```

### 1.6 Schema Filtering

```python
# Include only specific operations
filtered = schema.include(
    func: MatcherFunc | None = None,     # Custom filter function
    name: FilterValue | None = None,
    name_regex: str | None = None,
    method: FilterValue | None = None,    # e.g., "GET", ["GET", "POST"]
    method_regex: str | None = None,
    path: FilterValue | None = None,      # e.g., "/users"
    path_regex: str | None = None,        # e.g., "/api/v1/.*"
    tag: FilterValue | None = None,
    tag_regex: RegexValue | None = None,
    operation_id: FilterValue | None = None,
    operation_id_regex: RegexValue | None = None,
)

# Exclude specific operations (same parameters)
filtered = schema.exclude(
    ...,
    deprecated: bool = False,  # Also exclude deprecated operations
)

# Chain: include users endpoints, exclude DELETE
schema.include(path_regex="/users.*").exclude(method="DELETE")
```

### 1.7 API Operation Access

```python
# Access specific operation
operation = schema["/users"]["GET"]  # Returns APIOperation

# Check if response is valid
is_valid: bool = operation.is_valid_response(response)

# Validate response (raises FailureGroup on failure)
operation.validate_response(response, case=None)

# Create a specific test case manually
case = operation.Case(
    method: str | None = None,
    path_parameters: dict | None = None,
    headers: dict | None = None,
    cookies: dict | None = None,
    query: dict | None = None,
    body: Any = NOT_SET,
    media_type: str | None = None,
)

# Get Hypothesis strategy for an operation
strategy = operation.as_strategy(
    generation_mode: GenerationMode = GenerationMode.POSITIVE,
    **kwargs: Any,
) -> SearchStrategy
```

### 1.8 Stateful Testing

```python
# Create state machine from schema (uses OpenAPI links)
StateMachine = schema.as_state_machine()
# Returns: type[APIStateMachine]

# Run stateful tests
StateMachine.run(settings=None)  # Optional Hypothesis settings

# Custom state machine with hooks
class CustomStateMachine(schema.as_state_machine()):
    def setup(self):
        """Called once at beginning of each scenario."""
        pass

    def teardown(self):
        """Called once at end of each scenario."""
        pass

    def before_call(self, case: Case):
        """Called before each API operation."""
        if case.headers is None:
            case.headers = {}
        case.headers["Authorization"] = "Bearer test-token"

    def after_call(self, response: Response, case: Case):
        """Called after each API operation."""
        pass

    def get_call_kwargs(self, case: Case) -> dict[str, Any]:
        """Returns kwargs for case.call()."""
        return {"timeout": 10}

    def validate_response(
        self,
        response: Response,
        case: Case,
        additional_checks: list[CheckFunction] | None = None,
        **kwargs: Any,
    ):
        """Validates response using configured checks."""
        super().validate_response(response, case, additional_checks)

CustomStateMachine.run()
```

### 1.9 Custom Checks

```python
import schemathesis

# Register a global custom check
@schemathesis.check
def check_cors_headers(ctx: CheckContext, response: Response, case: Case):
    """Verify CORS headers are present."""
    if "Access-Control-Allow-Origin" not in response.headers:
        raise AssertionError("Missing CORS headers")

# CheckContext provides:
ctx.config  # Configuration settings for validation checks
```

### 1.10 Hooks

```python
# Global hooks (auto-detected name)
@schemathesis.hook
def filter_query(ctx: HookContext, query):
    """Skip cases where query is None or invalid."""
    return query and "user_id" in query

@schemathesis.hook
def before_call(ctx: HookContext, case, **kwargs):
    """Modify headers before sending each request."""
    if case.headers is None:
        case.headers = {}
    case.headers["X-Test-Mode"] = "true"
    return None

# Named hooks
@schemathesis.hook("map_headers")
def add_custom_header(ctx: HookContext, headers):
    """Inject a test header into every request."""
    if headers is None:
        headers = {}
    headers["X-Custom"] = "value"
    return headers

# Schema-level hooks
@schema.hook("before_call")
def schema_specific_hook(ctx, case, **kwargs):
    pass

# HookContext provides:
ctx.operation  # API operation currently being processed
```

### 1.11 Authentication

```python
@schemathesis.auth(
    refresh_interval: int | None = 300,  # Seconds between refreshes (None = no caching)
    cache_by_key: CacheKeyFunction | None = None,
)
class TokenAuth:
    def get(self, case: Case, context: AuthContext) -> Any:
        """Fetch fresh authentication token."""
        response = requests.post(
            "http://localhost:8000/auth/token",
            json={"username": "demo", "password": "test"}
        )
        return response.json()["access_token"]

    def set(self, case: Case, data: Any, context: AuthContext):
        """Apply token to test case headers."""
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Bearer {data}"

# AuthContext provides:
context.operation  # Current API operation
context.app        # Python app instance (ASGI/WSGI), or None
```

### 1.12 Custom Formats and Media Types

```python
from hypothesis import strategies as st

# Register custom string format
schemathesis.openapi.format("phone", st.from_regex(r"\+1-\d{3}-\d{3}-\d{4}"))

# Register custom media type strategy
schemathesis.openapi.media_type("application/pdf", pdf_strategy)
schemathesis.openapi.media_type("application/xml", xml_strategy, aliases=("text/xml",))
```

### 1.13 Targeted Property-Based Testing

```python
@schemathesis.metric
def response_size(ctx: MetricContext) -> float:
    """Guide generation toward larger responses."""
    return float(len(ctx.response.content))

# MetricContext provides:
ctx.case      # Generated test case
ctx.response  # HTTP response from server
```

### 1.14 Hypothesis Integration

```python
from hypothesis import given, settings
import schemathesis

schema = schemathesis.openapi.from_url("http://localhost:8000/openapi.json")

# Use operation strategy with @given
@given(case=schema["/users"]["POST"].as_strategy())
@settings(max_examples=50)
def test_create_user(case):
    response = case.call()
    assert response.status_code in (201, 422)

# Combined schema strategy
@given(case=schema.as_strategy(generation_mode=GenerationMode.POSITIVE))
def test_all_positive(case):
    case.call_and_validate()
```

### 1.15 CLI Reference

```bash
# Basic usage
st run <SCHEMA_URL_OR_PATH> [OPTIONS]

# Key options:
st run openapi.yaml --url https://api.example.com  # Base URL (required for files)
st run openapi.yaml --workers 4                     # Concurrent workers (1-64 or "auto")
st run openapi.yaml --phases examples,fuzzing       # Test phases: examples,coverage,fuzzing,stateful
st run openapi.yaml --wait-for-schema 10.0          # Wait for schema availability

# Validation:
st run openapi.yaml --checks all                    # all|not_a_server_error|status_code_conformance|
                                                    # content_type_conformance|response_headers_conformance|
                                                    # response_schema_conformance|negative_data_rejection|
                                                    # positive_data_acceptance|use_after_free|
                                                    # ensure_resource_availability|ignored_auth
st run openapi.yaml --exclude-checks response_schema_conformance
st run openapi.yaml --max-failures 5                # Stop after N failures
st run openapi.yaml --max-response-time 2.5         # Max response time in seconds

# Filtering:
st run openapi.yaml --include-tag users
st run openapi.yaml --exclude-method DELETE
st run openapi.yaml --include-path-regex "/api/v1/.*"
st run openapi.yaml --exclude-deprecated

# Network:
st run openapi.yaml --header "Authorization: Bearer token"
st run openapi.yaml --auth username:password
st run openapi.yaml --rate-limit 100/m              # 100 requests per minute
st run openapi.yaml --request-timeout 5.0           # Default: 10.0

# Data generation:
st run openapi.yaml --mode all                      # positive|negative|all
st run openapi.yaml --max-examples 100
st run openapi.yaml --seed 42                       # Reproducible runs
st run openapi.yaml --generation-maximize response_time

# Reports:
st run openapi.yaml --report junit,har              # junit|vcr|har|ndjson
st run openapi.yaml --report-dir ./test-reports

# Exit codes:
# 0 = all checks passed
# 1 = at least one check failed
# 2 = configuration/schema errors
```

### 1.16 Response Object

```python
# schemathesis.Response (wrapper around transport responses)
response.status_code: int          # HTTP status code
response.headers: dict             # Lowercase keys
response.content: bytes            # Raw body
response.text: str                 # Decoded text
response.encoding: str | None      # Character encoding
response.elapsed: float            # Response time in seconds
response.http_version: str         # "1.0" or "1.1"
response.message: str              # Status message
response.body_size: int | None     # Body size in bytes
response.encoded_body: str         # Base64 encoded body
response.json() -> Any             # Parse JSON (raises JSONDecodeError)
response.request: Request          # Original request
response.verify: bool              # TLS verification status
```

---

## 2. Pact Python v3 (pact-python 3.2.1)

### 2.1 Installation

```bash
pip install pact-python
# Current: v3.2.1 (Pact Specification V4, native Rust FFI)
```

### 2.2 Consumer Contract Testing

#### Pact Class

```python
from pact import Pact, match

# Create a consumer contract
pact = Pact(
    consumer: str,   # Consumer name (non-empty)
    provider: str,   # Provider name (non-empty)
)

# Properties
pact.consumer: str                          # Consumer name
pact.provider: str                          # Provider name
pact.specification: PactSpecification       # Pact spec version

# Methods
pact.with_specification(version: str) -> Self
# version: "V1", "V1_1", "V2", "V3", "V4"

pact.with_metadata(namespace: str, metadata: dict[str, str]) -> Self
# Add metadata to the Pact

pact.using_plugin(name: str, version: str | None = None) -> Self
# Add a plugin (e.g., protobuf, gRPC)
```

#### HTTP Interaction (Consumer Side)

```python
# Create an HTTP interaction
interaction = pact.upon_receiving(
    description: str,                        # Unique description
    interaction: Literal["HTTP"] = "HTTP",   # Interaction type
) -> HttpInteraction

# Chain methods on HttpInteraction:
(
    pact
    .upon_receiving("get user by ID")
    .given("user 123 exists")                                    # Provider state
    .given("user 123 exists", parameters={"id": "123"})          # With params
    .with_request(method="GET", path="/users/123")               # HTTP request
    .with_request(
        method: str,                    # HTTP method
        path: str,                      # URL path
        headers: dict | None = None,    # Request headers
        query: dict | None = None,      # Query parameters
        body: Any = None,               # Request body
    )
    .will_respond_with(                                          # Expected response
        status: int = 200,              # HTTP status code
        headers: dict | None = None,    # Response headers
        body: Any = None,               # Response body
    )
)
```

#### Matching DSL

```python
from pact import match, generate

# Matchers (match module) — use via module namespace to avoid shadowing built-ins
match.int(value: int = 0, *, min: int | None = None, max: int | None = None)
match.float(value: float = 0.0, *, precision: int | None = None)
match.str(value: str = "", *, size: int | None = None)
match.bool(value: bool = True)
match.date(value: str = "2000-01-01", *, format: str = "yyyy-MM-dd")
match.datetime(value: str = ..., *, format: str = ...)
match.time(value: str = ..., *, format: str = ...)
match.regex(value: str, *, regex: str)
match.uuid(value: str | None = None)
match.include(value: str)
match.each_like(value: Any, *, min: int | None = None, max: int | None = None)
match.like(value: Any)       # Type matching (any value of same type)
match.type(value: Any)       # Alias for like()

# Generators (generate module)
generate.uuid() -> str
generate.int(*, min: int | None = None, max: int | None = None)
generate.float(*, precision: int | None = None)
generate.date(*, format: str = "yyyy-MM-dd")
generate.datetime(*, format: str = ...)
generate.regex(regex: str)

# Example with matchers
body = {
    "id": match.int(123),
    "name": match.str("alice"),
    "email": match.regex("alice@example.com", regex=r".+@.+\..+"),
    "tags": match.each_like("admin", min=1),
    "metadata": match.like({"key": "value"}),
}
```

#### Mock Server (Consumer Testing)

```python
# Serve mock for consumer testing
server = pact.serve(
    addr: str = "localhost",
    port: int = 0,               # 0 = random port
    transport: str = "http",
    transport_config: str | None = None,  # JSON string
    *,
    raises: bool = True,         # Raise on mismatches
    verbose: bool = True,        # Log mismatches
) -> PactServer

# Use as context manager
with pact.serve() as srv:
    # srv.url -> "http://localhost:<port>"
    # Make requests against srv.url
    response = requests.get(f"{srv.url}/users/123")
    assert response.status_code == 200
    # Pact file written on exit if all interactions matched
```

#### Message Interaction (Async/Sync)

```python
# Async message
async_interaction = pact.upon_receiving(
    "user created event",
    interaction="Async",
) -> AsyncMessageInteraction

# Sync message (request/response)
sync_interaction = pact.upon_receiving(
    "get user query",
    interaction="Sync",
) -> SyncMessageInteraction

# Verify message handling
pact.verify(
    handler: Callable[[str | bytes | None, dict[str, object]], None],
    kind: Literal["Async", "Sync"],
    *,
    raises: bool = True,
) -> list[InteractionVerificationError] | None
```

### 2.3 Provider Verification

```python
from pact import Verifier

# Create verifier
verifier = Verifier(
    name: str,                    # Provider name
    host: str | None = None,     # Deprecated, use add_transport
)

# Configure provider
verifier.add_transport(
    protocol: str = "http",      # Transport protocol
    port: int | None = None,     # Port number
    path: str | None = None,     # Base path
    scheme: str | None = None,   # URL scheme
    *,
    url: str | None = None,      # Full URL (alternative to individual params)
) -> Self

# Add pact sources
verifier.add_source(
    source: str | Path,          # Directory or file path with pact files
) -> Self

# Broker source (simple)
verifier.broker_source(
    url: str,                    # Pact Broker URL
    *,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    selector: bool = False,      # True = returns BrokerSelectorBuilder
) -> Self | BrokerSelectorBuilder

# Broker source with selectors
builder = verifier.broker_source(
    "https://broker.example.com",
    token="my-token",
    selector=True,
) -> BrokerSelectorBuilder

builder = (
    builder
    .consumer_version(main_branch=True)
    .consumer_version(deployed_or_released=True)
    .include_pending()
    .include_wip_since(date(2024, 1, 1))
    .provider_tags("main", "prod")
    .provider_branch("main")
    .build()  # Returns Verifier
)

# State change callback
verifier.set_state(
    url: str,                    # URL to POST state changes to
    *,
    teardown: bool = False,      # Whether to call teardown states
    body: bool = True,           # Send state in request body
) -> Self

# Provider info
verifier.set_info(
    name: str,                   # Provider name
    *,
    url: str | None = None,
    scheme: str | None = None,
    host: str | None = None,
    port: int | None = None,
    path: str | None = None,
) -> Self

# Filter interactions
verifier.filter(
    description: str | None = None,   # Filter by description
    state: str | None = None,         # Filter by provider state
    no_state: bool = False,           # Only interactions without state
) -> Self

# Set consumer filters
verifier.filter_consumers(*consumers: str) -> Self

# Logging and publish
verifier.set_publish_options(
    version: str,
    url: str | None = None,
    tags: list[str] | None = None,
    branch: str | None = None,
    build_url: str | None = None,
) -> Self

# Execute verification
verifier.verify() -> None  # Raises on failure
```

### 2.4 Complete Consumer-Provider Example

```python
# === consumer_test.py ===
import requests
from pact import Pact, match

def test_get_user():
    pact = Pact("UserConsumer", "UserProvider")
    (
        pact
        .upon_receiving("a request for user 123")
        .given("user 123 exists", parameters={"id": "123"})
        .with_request("GET", "/api/users/123")
        .will_respond_with(
            status=200,
            headers={"Content-Type": "application/json"},
            body={
                "id": match.int(123),
                "name": match.str("Alice"),
                "email": match.regex("alice@example.com", regex=r".+@.+"),
            },
        )
    )

    with pact.serve() as srv:
        response = requests.get(f"{srv.url}/api/users/123")
        assert response.status_code == 200
        user = response.json()
        assert user["name"] == "Alice"


# === provider_test.py ===
from pact import Verifier

def test_provider_verification():
    verifier = (
        Verifier("UserProvider")
        .add_transport(url="http://localhost:8080")
        .add_source("./pacts/")
        .set_state(url="http://localhost:8080/_pact/state", teardown=True)
    )
    verifier.verify()
```

### 2.5 Bidirectional Contract Testing with OpenAPI

Pact supports bidirectional contract testing where:
1. Consumer generates a Pact contract via the consumer test
2. Provider verifies against its OpenAPI spec (no need to run provider)
3. PactFlow broker compares both to find mismatches

```python
# Provider side: verify OpenAPI spec satisfies consumer pacts
# This is done through PactFlow (SaaS), not directly in pact-python
# The provider publishes its OpenAPI spec to PactFlow:
# pact-broker publish-provider-contract \
#   --provider "UserProvider" \
#   --contract openapi.yaml \
#   --content-type application/yaml \
#   --verification-exit-code 0 \
#   --verification-results verification-results.txt \
#   --verifier schemathesis
```

---

## 3. Testcontainers Python (v4.x)

### 3.1 Installation

```bash
pip install testcontainers[postgres,redis,compose]
# Modules: postgres, mysql, redis, mongodb, kafka, rabbitmq, compose, etc.
```

### 3.2 Basic Container Lifecycle

```python
from testcontainers.core.container import DockerContainer

# Generic container
container = DockerContainer("nginx:latest")
container.with_exposed_ports(80)
container.with_env("MY_VAR", "value")

# Start/stop manually
container.start()
port = container.get_exposed_port(80)
host = container.get_container_host_ip()
# ... use container ...
container.stop()

# Context manager (recommended)
with DockerContainer("nginx:latest") as container:
    container.with_exposed_ports(80)
    container.start()
    port = container.get_exposed_port(80)
    # Auto-stopped on exit
```

### 3.3 Database Containers

```python
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

# PostgreSQL — built-in wait for connection readiness
postgres = PostgresContainer(
    image="postgres:16",
    user="testuser",
    password="testpass",
    dbname="testdb",
)
with postgres:
    # postgres.start() auto-waits for readiness
    connection_url = postgres.get_connection_url()
    # "postgresql://testuser:testpass@localhost:<port>/testdb"

    host = postgres.get_container_host_ip()
    port = postgres.get_exposed_port(5432)

# Redis — built-in wait for connection
redis = RedisContainer()
with redis:
    redis_url = redis.get_connection_url()
```

### 3.4 Wait Strategies

```python
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import (
    LogMessageWaitStrategy,
    HttpWaitStrategy,
    PortWaitStrategy,
    ExecWaitStrategy,
)
from datetime import timedelta
import re

# Wait for log message (string or regex)
container = DockerContainer("postgres:16")
container.with_exposed_ports(5432)
container.with_env("POSTGRES_PASSWORD", "test")
container.waiting_for(
    LogMessageWaitStrategy("database system is ready to accept connections")
    .with_startup_timeout(timedelta(seconds=60))
    .with_poll_interval(0.5)
)

# Wait for HTTP endpoint
container.waiting_for(
    HttpWaitStrategy(80)
    .for_status_code(200)
    .for_path("/health")
    .with_startup_timeout(30)
)

# Wait for regex pattern in logs
container.waiting_for(
    LogMessageWaitStrategy(re.compile(r"Server listening on port \d+"))
)

# Wait for TCP port
container.waiting_for(PortWaitStrategy(6379))

# Wait for command execution
container.waiting_for(
    ExecWaitStrategy(
        ["sh", "-c", "PGPASSWORD='secret' psql -U postgres -c 'SELECT 1'"]
    ).with_startup_timeout(timedelta(seconds=60))
)
```

### 3.5 Docker Compose Integration

```python
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import HttpWaitStrategy, LogMessageWaitStrategy
import requests

# Basic usage
compose = DockerCompose(
    context="./",                              # Directory with docker-compose.yml
    compose_file_name="docker-compose.yml",    # Default filename
)

# With per-service wait strategies
with compose.waiting_for({
    "web": HttpWaitStrategy(8080).for_status_code(200).for_path("/ready"),
    "db": LogMessageWaitStrategy("database system is ready"),
    "cache": LogMessageWaitStrategy("Ready to accept connections"),
}):
    # All services are now ready
    web_host = compose.get_service_host("web", 8080)
    web_port = compose.get_service_port("web", 8080)

    response = requests.get(f"http://{web_host}:{web_port}/api/health")
    assert response.status_code == 200

    # Execute command in a service container
    stdout, stderr, exit_code = compose.exec_in_container(
        service_name="db",
        command=["psql", "-U", "app", "-d", "appdb", "-c", "SELECT COUNT(*) FROM users"],
    )
```

### 3.6 Custom Network Configuration

```python
from testcontainers.core.network import Network
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

# Create isolated network
network = Network()
network.create()

# Multi-container with network aliases
def test_multi_container_app():
    with Network() as network:
        postgres = PostgresContainer()
        postgres.with_network(network)
        postgres.with_network_aliases("db", "database")

        redis = RedisContainer()
        redis.with_network(network)
        redis.with_network_aliases("cache")

        with postgres, redis:
            db_host = postgres.get_container_host_ip()
            db_port = postgres.get_exposed_port(5432)
            redis_host = redis.get_container_host_ip()
            redis_port = redis.get_exposed_port(6379)
            # Containers can reach each other via aliases: "db", "cache"

# Custom network with Docker config
with Network(
    docker_network_kw={
        "driver": "bridge",
        "options": {"com.docker.network.bridge.name": "test-bridge"},
    }
) as custom_network:
    with DockerContainer("redis:latest") as redis:
        redis.with_network(custom_network)
        redis.with_exposed_ports(6379)
        redis.start()
```

### 3.7 Container Configuration Methods

```python
container = DockerContainer("image:tag")

# Port mapping
container.with_exposed_ports(80, 443)           # Expose ports to host

# Environment variables
container.with_env("KEY", "value")

# Volume mounts
container.with_volume_mapping(
    host_path="/host/path",
    container_path="/container/path",
    mode="rw",                                   # "rw" or "ro"
)

# Network
container.with_network(network)
container.with_network_aliases("alias1", "alias2")

# Command override
container.with_command("custom command args")

# Container name
container.with_name("my-container")

# Bind mount
container.with_bind_ports(host_port=8080, container_port=80)

# Get connection info
host = container.get_container_host_ip()
port = container.get_exposed_port(80)

# Execute command in running container
result = container.exec(["ls", "-la"])
```

---

## 4. pytest + httpx Async Testing

### 4.1 Installation

```bash
pip install httpx pytest-asyncio
```

### 4.2 httpx.AsyncClient Core API

```python
import httpx

# Basic async usage
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/users")

# With base URL and timeout
async with httpx.AsyncClient(
    base_url="http://localhost:8000",
    timeout=httpx.Timeout(
        10.0,            # Default for all operations
        connect=5.0,     # Connection establishment
        read=30.0,       # Reading response
        write=10.0,      # Sending request
        pool=5.0,        # Acquiring connection from pool
    ),
    headers={"Authorization": "Bearer token"},
) as client:
    response = await client.get("/users")
    response = await client.post("/users", json={"name": "Alice"})
    response = await client.put("/users/1", json={"name": "Bob"})
    response = await client.patch("/users/1", json={"email": "bob@example.com"})
    response = await client.delete("/users/1")
```

### 4.3 Concurrent Requests

```python
import httpx
import asyncio

async def test_concurrent_requests():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        urls = ["/api/users", "/api/products", "/api/orders"]
        responses = await asyncio.gather(*[client.get(url) for url in urls])
        for r in responses:
            assert r.status_code == 200
```

### 4.4 Mock Transport for Testing

```python
import httpx

def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/users":
        return httpx.Response(200, json=[{"id": 1, "name": "Alice"}])
    return httpx.Response(404)

# Use MockTransport for unit testing without network
transport = httpx.MockTransport(handler)
client = httpx.Client(transport=transport)
response = client.get("http://testserver/users")
assert response.status_code == 200

# Async mock transport
async_transport = httpx.MockTransport(handler)
async with httpx.AsyncClient(transport=async_transport) as client:
    response = await client.get("http://testserver/users")
```

### 4.5 ASGI Transport (Direct App Testing)

```python
import httpx
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

async def hello(request):
    return HTMLResponse("Hello World!")

app = Starlette(routes=[Route("/", hello)])

# Test ASGI app directly (no network)
transport = httpx.ASGITransport(app=app)
async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
    r = await client.get("/")
    assert r.status_code == 200
    assert r.text == "Hello World!"
```

### 4.6 pytest-asyncio Integration

```python
import pytest
import httpx

# Configure pytest-asyncio mode in pyproject.toml:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"

# Async test (auto mode - no decorator needed)
async def test_api_health():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/health")
        assert response.status_code == 200

# Async fixture
@pytest.fixture
async def api_client():
    async with httpx.AsyncClient(
        base_url="http://localhost:8000",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client

async def test_get_users(api_client: httpx.AsyncClient):
    response = await api_client.get("/api/users")
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
```

### 4.7 Parametrized Endpoint Testing

```python
import pytest
import httpx

@pytest.fixture
async def client():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as c:
        yield c

@pytest.mark.parametrize("endpoint,expected_status", [
    ("/api/users", 200),
    ("/api/products", 200),
    ("/api/orders", 200),
    ("/api/nonexistent", 404),
])
async def test_endpoints(client: httpx.AsyncClient, endpoint: str, expected_status: int):
    response = await client.get(endpoint)
    assert response.status_code == expected_status

@pytest.mark.parametrize("method,path,body,expected", [
    ("POST", "/api/users", {"name": "Alice"}, 201),
    ("POST", "/api/users", {}, 422),
    ("POST", "/api/users", {"name": ""}, 422),
])
async def test_create_user_validation(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    body: dict,
    expected: int,
):
    response = await client.request(method, path, json=body)
    assert response.status_code == expected
```

### 4.8 Multi-Service Test Setup

```python
import pytest
import httpx
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import HttpWaitStrategy

@pytest.fixture(scope="session")
def services():
    """Start all services via Docker Compose."""
    compose = DockerCompose("./", compose_file_name="docker-compose.test.yml")
    with compose.waiting_for({
        "api-gateway": HttpWaitStrategy(8080).for_status_code(200).for_path("/health"),
        "user-service": HttpWaitStrategy(8081).for_status_code(200).for_path("/health"),
        "order-service": HttpWaitStrategy(8082).for_status_code(200).for_path("/health"),
    }):
        yield {
            "gateway": f"http://{compose.get_service_host('api-gateway', 8080)}:{compose.get_service_port('api-gateway', 8080)}",
            "users": f"http://{compose.get_service_host('user-service', 8081)}:{compose.get_service_port('user-service', 8081)}",
            "orders": f"http://{compose.get_service_host('order-service', 8082)}:{compose.get_service_port('order-service', 8082)}",
        }

@pytest.fixture
async def gateway_client(services):
    async with httpx.AsyncClient(base_url=services["gateway"]) as client:
        yield client

@pytest.fixture
async def user_client(services):
    async with httpx.AsyncClient(base_url=services["users"]) as client:
        yield client

async def test_cross_service_user_creation(gateway_client, user_client):
    # Create user via gateway
    response = await gateway_client.post("/api/users", json={"name": "Alice"})
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Verify directly on user service
    response = await user_client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Alice"
```

### 4.9 Test Result Collection

```python
import pytest
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict

@dataclass
class TestResult:
    name: str
    status: str  # "passed", "failed", "error"
    duration: float
    error: str | None = None
    endpoint: str | None = None

@dataclass
class TestReport:
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    results: list[TestResult] = field(default_factory=list)

    def add(self, result: TestResult):
        self.results.append(result)
        self.total += 1
        if result.status == "passed":
            self.passed += 1
        elif result.status == "failed":
            self.failed += 1
        else:
            self.errors += 1

    def save(self, path: str):
        Path(path).write_text(json.dumps(asdict(self), indent=2))

# pytest plugin for collecting results
class ResultCollector:
    def __init__(self):
        self.report = TestReport()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if report.when == "call":
            self.report.add(TestResult(
                name=item.name,
                status="passed" if report.passed else "failed",
                duration=report.duration,
                error=str(report.longrepr) if report.failed else None,
                endpoint=getattr(item, "endpoint", None),
            ))

# Usage in conftest.py
def pytest_configure(config):
    collector = ResultCollector()
    config.pluginmanager.register(collector, "result_collector")
    config._result_collector = collector

def pytest_unconfigure(config):
    collector = getattr(config, "_result_collector", None)
    if collector:
        collector.report.save("test-results.json")
```

---

## 5. Integration Patterns

### 5.1 Schemathesis + Testcontainers: Schema Conformance Testing

```python
import pytest
import schemathesis
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import HttpWaitStrategy

@pytest.fixture(scope="session")
def api_service():
    """Start service with Testcontainers, test with Schemathesis."""
    compose = DockerCompose("./")
    with compose.waiting_for({
        "api": HttpWaitStrategy(8080).for_status_code(200).for_path("/health"),
    }):
        host = compose.get_service_host("api", 8080)
        port = compose.get_service_port("api", 8080)
        yield f"http://{host}:{port}"

@pytest.fixture
def api_schema(api_service):
    return schemathesis.openapi.from_url(
        f"{api_service}/openapi.json",
        wait_for_schema=10.0,
    )

# Use fixture-based schema
schema = schemathesis.pytest.from_fixture("api_schema")

@schema.parametrize()
def test_schema_conformance(case):
    """Every endpoint conforms to its OpenAPI schema."""
    case.call_and_validate()
```

### 5.2 Pact + Schemathesis: Contract + Schema Testing

```python
# Step 1: Consumer generates Pact contract
# Step 2: Provider verifies Pact contract
# Step 3: Schemathesis fuzz-tests provider against OpenAPI schema

import schemathesis
from pact import Verifier

def test_provider_pact_compliance():
    """Verify provider satisfies consumer contracts."""
    verifier = (
        Verifier("OrderService")
        .add_transport(url="http://localhost:8082")
        .add_source("./pacts/")
        .set_state(url="http://localhost:8082/_pact/state", teardown=True)
    )
    verifier.verify()

# Then fuzz the same service
schema = schemathesis.openapi.from_url("http://localhost:8082/openapi.json")

@schema.parametrize()
def test_schema_fuzz(case):
    """Fuzz test all endpoints beyond contract expectations."""
    case.call_and_validate()
```

### 5.3 Full Integration: Testcontainers + Schemathesis + httpx + Pact

```python
import pytest
import httpx
import schemathesis
from pact import Pact, Verifier, match
from testcontainers.compose import DockerCompose
from testcontainers.core.waiting_utils import HttpWaitStrategy

# --- Fixture: Start all services ---
@pytest.fixture(scope="session")
def services():
    compose = DockerCompose("./", compose_file_name="docker-compose.test.yml")
    with compose.waiting_for({
        "user-service": HttpWaitStrategy(8081).for_status_code(200).for_path("/health"),
        "order-service": HttpWaitStrategy(8082).for_status_code(200).for_path("/health"),
    }):
        yield {
            "users": f"http://{compose.get_service_host('user-service', 8081)}:{compose.get_service_port('user-service', 8081)}",
            "orders": f"http://{compose.get_service_host('order-service', 8082)}:{compose.get_service_port('order-service', 8082)}",
        }

# --- Layer 1: Consumer contract tests ---
def test_order_service_expects_user_service():
    pact = Pact("OrderService", "UserService")
    (
        pact
        .upon_receiving("get user for order validation")
        .given("user 1 exists")
        .with_request("GET", "/api/users/1")
        .will_respond_with(
            status=200,
            body={"id": match.int(1), "name": match.str("Alice"), "active": match.bool(True)},
        )
    )
    with pact.serve() as srv:
        response = httpx.get(f"{srv.url}/api/users/1")
        assert response.status_code == 200

# --- Layer 2: Provider verification ---
def test_user_service_satisfies_contracts(services):
    verifier = (
        Verifier("UserService")
        .add_transport(url=services["users"])
        .add_source("./pacts/")
        .set_state(url=f"{services['users']}/_pact/state")
    )
    verifier.verify()

# --- Layer 3: Schema conformance (fuzz) ---
@pytest.fixture
def user_schema(services):
    return schemathesis.openapi.from_url(f"{services['users']}/openapi.json")

schema = schemathesis.pytest.from_fixture("user_schema")

@schema.parametrize()
def test_user_service_schema(case):
    case.call_and_validate()

# --- Layer 4: Cross-service integration ---
async def test_create_order_cross_service(services):
    async with httpx.AsyncClient() as client:
        # Create user
        user_resp = await client.post(
            f"{services['users']}/api/users",
            json={"name": "TestUser", "email": "test@example.com"},
        )
        assert user_resp.status_code == 201
        user_id = user_resp.json()["id"]

        # Create order referencing user
        order_resp = await client.post(
            f"{services['orders']}/api/orders",
            json={"user_id": user_id, "items": [{"product_id": 1, "quantity": 2}]},
        )
        assert order_resp.status_code == 201

        # Verify order references correct user
        order = await client.get(f"{services['orders']}/api/orders/{order_resp.json()['id']}")
        assert order.json()["user_id"] == user_id
```

---

## 6. Error Handling Patterns

### 6.1 Schemathesis Error Handling

```python
import schemathesis
from schemathesis.exceptions import CheckFailed

schema = schemathesis.openapi.from_url("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_with_error_handling(case):
    try:
        response = case.call_and_validate()
    except CheckFailed as e:
        # Specific check failures
        print(f"Check failed: {e}")
        print(f"Curl command: {case.as_curl_command()}")
        raise
    except Exception as e:
        # Network errors, timeouts, etc.
        pytest.skip(f"Transient error: {e}")
```

### 6.2 Pact Error Handling

```python
from pact import Pact, Verifier
from pact.error import PactVerificationError, InteractionVerificationError

# Consumer: handle mismatches
pact = Pact("Consumer", "Provider")
# ... define interactions ...

with pact.serve(raises=False) as srv:
    # mismatches won't raise, check manually
    response = requests.get(f"{srv.url}/api/users")

# Provider: handle verification failure
try:
    verifier = Verifier("Provider").add_transport(url="http://localhost:8080")
    verifier.add_source("./pacts/")
    verifier.verify()
except PactVerificationError as e:
    print(f"Provider verification failed: {e}")

# Message: collect errors
errors = pact.verify(handler, kind="Async", raises=False)
if errors:
    for err in errors:
        print(f"Interaction '{err.description}' failed: {err.error}")
```

### 6.3 Testcontainers Error Handling

```python
from testcontainers.core.container import DockerContainer
from testcontainers.core.exceptions import ContainerStartException
import docker.errors

try:
    with DockerContainer("nonexistent-image:latest") as container:
        container.start()
except (ContainerStartException, docker.errors.ImageNotFound) as e:
    print(f"Container failed to start: {e}")

# Timeout handling
from datetime import timedelta
container.waiting_for(
    LogMessageWaitStrategy("ready")
    .with_startup_timeout(timedelta(seconds=30))
)
# Raises TimeoutError if container doesn't become ready
```

---

## 7. Version Compatibility

| Library | Python | Key Dependencies |
|---------|--------|-----------------|
| Schemathesis 4.x | >=3.9 | requests, hypothesis, jsonschema, pyyaml |
| pact-python 3.2.1 | >=3.9 | pact-ffi (native Rust) |
| testcontainers 4.x | >=3.9 | docker-py, wrapt |
| httpx 0.28.x | >=3.9 | httpcore, anyio, certifi |
| pytest-asyncio 0.24.x | >=3.9 | pytest>=7.0 |

### Configuration Files

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"           # Auto-detect async tests
markers = [
    "integration: integration tests",
    "contract: contract tests",
    "schema: schema conformance tests",
]

[tool.schemathesis]
# Can also use schemathesis.toml or .schemathesis.toml
base_url = "http://localhost:8000"
checks = ["all"]
max_response_time = 5.0
workers = 4
```

```yaml
# schemathesis.yml (alternative)
base_url: http://localhost:8000
checks:
  - not_a_server_error
  - response_schema_conformance
max_examples: 100
phases:
  - examples
  - coverage
  - fuzzing
```
