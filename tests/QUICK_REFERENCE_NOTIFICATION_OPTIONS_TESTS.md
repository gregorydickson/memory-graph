# Quick Reference: NotificationOptions Bug Fix Tests

## Bug Fixed
**File**: `src/memorygraph/server.py`, lines 850-857
**Issue**: `notification_options=None` caused `AttributeError` in `get_capabilities()`
**Fix**: Use `NotificationOptions()` and `experimental_capabilities={}` instead

---

## Test File
`tests/test_server_main_initialization.py` - 15 tests, all passing

---

## Test Organization

### 🎯 Core Bug Fix Tests (TestNotificationOptionsInitialization)

| Test | What It Validates | Why It Matters |
|------|-------------------|----------------|
| `test_notification_options_is_not_none` | NotificationOptions() is passed, not None | Prevents the exact bug that was fixed |
| `test_get_capabilities_called_with_notification_options` | get_capabilities receives proper instance | Ensures type safety |
| `test_experimental_capabilities_is_empty_dict` | experimental_capabilities is {}, not None | Prevents similar bugs |
| `test_no_attribute_error_during_initialization` | No AttributeError raised during init | **Regression test for the actual bug** |

### 🔧 Main Function Tests (TestMainFunctionInitialization)

| Test | What It Validates |
|------|-------------------|
| `test_main_creates_server_instance` | ClaudeMemoryServer is instantiated |
| `test_main_initializes_server` | server.initialize() is called |
| `test_main_calls_cleanup_on_exit` | cleanup happens on normal exit |
| `test_main_cleanup_on_exception` | cleanup happens even on errors |

### 📋 Parameter Tests (TestInitializationOptionsParameters)

| Test | What It Validates |
|------|-------------------|
| `test_initialization_options_server_name` | server_name = "claude-memory" |
| `test_initialization_options_server_version` | server_version = "0.1.0" |
| `test_initialization_options_capabilities_object` | capabilities object exists |

### 🔗 Integration Tests (TestServerRunIntegration)

| Test | What It Validates |
|------|-------------------|
| `test_server_run_receives_streams` | read/write streams passed to run() |
| `test_server_run_receives_initialization_options` | InitializationOptions passed correctly |

### ✅ Instance Tests (TestNotificationOptionsInstance)

| Test | What It Validates |
|------|-------------------|
| `test_notification_options_can_be_instantiated` | NotificationOptions() creates valid instance |
| `test_notification_options_has_no_attribute_error` | Instance is safe to use (vs None) |

---

## Running the Tests

```bash
# Run all new tests
pytest tests/test_server_main_initialization.py -v

# Run specific test class
pytest tests/test_server_main_initialization.py::TestNotificationOptionsInitialization -v

# Run a single test
pytest tests/test_server_main_initialization.py::TestNotificationOptionsInitialization::test_no_attribute_error_during_initialization -v

# Run with all server tests
pytest tests/test_server*.py -v
```

---

## Test Coverage Summary

✅ **15/15 tests passing**

**Code paths covered**:
- Main function initialization flow
- NotificationOptions proper instantiation
- experimental_capabilities dict initialization
- InitializationOptions construction
- server.run() parameter passing
- Error handling and cleanup

**Regression protection**: Tests will fail if:
- Someone changes back to `notification_options=None`
- Someone changes back to `experimental_capabilities=None`
- The main() function lifecycle breaks
- Cleanup stops working

---

## Key Test Patterns Used

### 1. Async Context Manager Mocking
```python
@asynccontextmanager
async def mock_stdio_context():
    read_stream = AsyncMock()
    write_stream = AsyncMock()
    yield read_stream, write_stream
```

### 2. Type Verification
```python
assert notification_options is not None
assert isinstance(notification_options, NotificationOptions)
```

### 3. Cleanup Testing
```python
try:
    await main()
except KeyboardInterrupt:
    pass

# Verify cleanup was called even after interrupt
mock_cleanup.assert_called_once()
```

---

## Integration with Codebase

These tests follow the existing patterns from:
- `tests/test_server_init.py` - Server initialization patterns
- `tests/test_server.py` - Handler testing patterns

**Dependencies**: pytest, pytest-asyncio, unittest.mock

**No external dependencies required**: Tests use mocks, no database needed
