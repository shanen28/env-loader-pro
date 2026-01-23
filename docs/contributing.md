# Contributing

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/shanen28/env-loader-pro.git
cd env-loader-pro

# Install in development mode
pip install -e ".[test,all]"

# Run tests
pytest tests/ -v
```

### Project Structure

```
env_loader_pro/
├── core/           # Core functionality
├── providers/      # Configuration providers
├── crypto/         # Encryption support
├── exporters/      # Configuration exporters
└── utils/          # Utilities

tests/              # Test suite
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_loader.py -v

# Run with coverage
pytest tests/ --cov=src/env_loader_pro --cov-report=html
```

## Coding Standards

### Type Hints

All functions must have type hints:

```python
def load_env(
    env: Optional[str] = None,
    path: str = ".env",
    strict: bool = False,
) -> Dict[str, Any]:
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def my_function(param: str) -> int:
    """Brief description.
    
    Args:
        param: Parameter description
    
    Returns:
        Return value description
    
    Raises:
        ValueError: When parameter is invalid
    """
    ...
```

### Error Handling

Use custom exceptions from `exceptions.py`:

```python
from env_loader_pro.exceptions import EnvLoaderError, ValidationError

if not value:
    raise ValidationError(f"Invalid value: {value}")
```

### Secret Safety

**Never:**
- Log secret values
- Include secrets in error messages
- Store secrets in plaintext
- Commit secrets to git

**Always:**
- Use `safe_repr()` for logging
- Mask secrets in outputs
- Use audit trail for tracking

## Adding a New Provider

### 1. Create Provider Class

```python
from env_loader_pro.providers import BaseProvider
from env_loader_pro.exceptions import ProviderError

class MyProvider(BaseProvider):
    def __init__(self, config: str):
        self.config = config
    
    def get(self, key: str) -> Optional[str]:
        """Get single value."""
        try:
            return fetch_from_source(key)
        except Exception as e:
            raise ProviderError(f"Failed to get {key}: {e}")
    
    def get_many(self, keys: list[str]) -> Dict[str, str]:
        """Get multiple values."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value:
                result[key] = value
        return result
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return check_availability()
```

### 2. Register Provider

Add to `src/env_loader_pro/providers/__init__.py`:

```python
try:
    from .my_provider import MyProvider
except ImportError:
    MyProvider = None
```

### 3. Add Tests

Create `tests/test_my_provider.py`:

```python
def test_my_provider():
    provider = MyProvider(config="test")
    assert provider.is_available()
    value = provider.get("TEST_KEY")
    assert value is not None
```

### 4. Update Documentation

Add provider to documentation.

## Reporting Bugs

### Before Reporting

1. Check existing issues
2. Verify bug with latest version
3. Test with minimal example

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- Python version
- OS
- env-loader-pro version

**Minimal Example**
```python
# Minimal code to reproduce
```
```

## Feature Requests

### Before Requesting

1. Check existing issues
2. Verify feature doesn't exist
3. Consider use case

### Feature Request Template

```markdown
**Use Case**
Why is this feature needed?

**Proposed Solution**
How should it work?

**Alternatives**
Other approaches considered

**Additional Context**
Any other relevant information
```

## Pull Request Process

### Before Submitting

1. **Update tests** - Add tests for new features
2. **Update docs** - Update documentation if needed
3. **Run tests** - Ensure all tests pass
4. **Check linting** - No linter errors

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Docstrings added
- [ ] No secrets in code
- [ ] Backward compatible (if applicable)
- [ ] All tests passing

### PR Title Format

```
feat: Add new provider for X
fix: Resolve issue with Y
docs: Update documentation for Z
```

## Security

### Security Issues

**Do NOT** open public issues for security vulnerabilities. Email: shanen.j.thomas@gmail.com

### Security Checklist

- [ ] No secrets in code
- [ ] No secrets in tests
- [ ] Proper error handling
- [ ] Input validation
- [ ] Secret masking in place

## Development Priorities

1. **Security** - Never compromise on security
2. **Backward Compatibility** - Don't break existing code
3. **Performance** - Maintain performance guarantees
4. **Documentation** - Keep docs accurate
5. **Testing** - Maintain test coverage

## Questions?

- Open an issue for questions
- Check existing documentation
- Review code examples

Thank you for contributing! 🎉
