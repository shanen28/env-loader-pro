# Installation

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Basic Installation

```bash
pip install env-loader-pro
```

## Optional Dependencies

Install additional features as needed:

```bash
# For Pydantic schema support
pip install env-loader-pro[pydantic]

# For Azure Key Vault integration
pip install env-loader-pro[azure]

# For AWS Secrets Manager integration
pip install env-loader-pro[aws]

# For YAML export support
pip install env-loader-pro[yaml]

# For live reloading (watchdog)
pip install env-loader-pro[watch]

# For FastAPI integration
pip install env-loader-pro[fastapi]

# Install everything
pip install env-loader-pro[all]
```

## Development Installation

For contributing or development:

```bash
# Clone repository
git clone https://github.com/shanen28/env-loader-pro.git
cd env-loader-pro

# Install in editable mode with test dependencies
pip install -e ".[test,all]"

# Run tests
pytest tests/ -v
```

## Verify Installation

```bash
# Check version
python -c "from env_loader_pro import __version__; print(__version__)"

# Test CLI
envloader --help

# Test import
python -c "from env_loader_pro import load_env; print('✓ Installation successful')"
```

## Upgrade

```bash
pip install --upgrade env-loader-pro
```
