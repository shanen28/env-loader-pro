# Changelog

All notable changes to env-loader-pro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - TBD

### Added
- Pydantic schema support via `load_with_schema()`
- Dataclass schema support
- Case-insensitive matching between uppercase env vars and lowercase schema fields
- Enhanced type safety with schema validation

### Changed
- Improved error messages for schema validation
- Better handling of optional fields in schemas

## [0.2.0] - TBD

### Added
- Environment variable expansion (`${VAR}` syntax)
- Multiple environment support (`.env.dev`, `.env.prod`, etc.)
- List parsing (JSON arrays and comma-separated values)
- Runtime validation rules
- Strict mode for unknown variables
- Export to JSON/YAML
- Auto-generate `.env.example` files
- CLI tool (`envloader` command)
- Priority control (file vs system environment)

### Changed
- Improved default value handling to preserve types
- Enhanced secret masking patterns
- Better error messages

## [0.1.0] - TBD

### Added
- Initial release
- Basic environment loading from `.env` files
- Automatic type casting (int, bool, float, str)
- Required variable validation
- Default values support
- Secret masking for safe logging
- Safe representation method
- System environment variable support
- Configurable priority (file vs system)

---

[0.3.0]: https://github.com/yourusername/env-loader-pro/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourusername/env-loader-pro/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/env-loader-pro/releases/tag/v0.1.0

