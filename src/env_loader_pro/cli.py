"""CLI tool for env-loader-pro."""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

def main():
    parser = argparse.ArgumentParser(
        description="env-loader-pro: Typed, validated environment variable loader"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show environment variables")
    show_parser.add_argument("--env", help="Environment name (e.g., dev, prod)")
    show_parser.add_argument("--path", default=".env", help="Path to .env file")
    show_parser.add_argument("--format", choices=["json", "yaml", "pretty"], default="pretty")
    show_parser.add_argument("--unmask", action="store_true", help="Show unmasked values")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export config to file")
    export_parser.add_argument("--env", help="Environment name")
    export_parser.add_argument("--path", default=".env", help="Path to .env file")
    export_parser.add_argument("--format", choices=["json", "yaml"], default="json")
    export_parser.add_argument("--output", required=True, help="Output file path")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate environment variables")
    validate_parser.add_argument("--env", help="Environment name")
    validate_parser.add_argument("--path", default=".env", help="Path to .env file")
    validate_parser.add_argument("--required", nargs="+", help="Required variables")
    validate_parser.add_argument("--ci", action="store_true", help="CI mode: no cloud access, fail on errors")
    validate_parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    
    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Show configuration audit trail")
    audit_parser.add_argument("--env", help="Environment name")
    audit_parser.add_argument("--path", default=".env", help="Path to .env file")
    audit_parser.add_argument("--json", action="store_true", help="Output as JSON")
    audit_parser.add_argument("--ci", action="store_true", help="CI mode: no cloud access")
    
    # Explain command
    explain_parser = subparsers.add_parser("explain", help="Explain configuration precedence and policies")
    explain_parser.add_argument("--env", help="Environment name")
    explain_parser.add_argument("--path", default=".env", help="Path to .env file")
    explain_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    
    # Diff command (Phase 3)
    diff_parser = subparsers.add_parser("diff", help="Compare configuration changes")
    diff_parser.add_argument("--env", help="Environment name")
    diff_parser.add_argument("--path", default=".env", help="Path to .env file")
    diff_parser.add_argument("--baseline", help="Baseline configuration file")
    diff_parser.add_argument("--deny-secret-changes", action="store_true", help="Fail if secrets added/removed")
    diff_parser.add_argument("--ci", action="store_true", help="CI mode: no cloud access")
    
    # Encrypt/decrypt commands
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt .env file")
    encrypt_parser.add_argument("input", help="Input file path")
    encrypt_parser.add_argument("--output", help="Output file path")
    encrypt_parser.add_argument("--method", choices=["age", "gpg"], default="age", help="Encryption method")
    encrypt_parser.add_argument("--key", help="Path to encryption key")
    
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt .env file")
    decrypt_parser.add_argument("input", help="Input encrypted file path")
    decrypt_parser.add_argument("--output", help="Output file path")
    decrypt_parser.add_argument("--key", help="Path to decryption key")
    
    # Generate example command
    gen_parser = subparsers.add_parser("generate-example", help="Generate .env.example file")
    gen_parser.add_argument("--output", default=".env.example", help="Output file path")
    gen_parser.add_argument("--required", nargs="+", help="Required variables")
    gen_parser.add_argument("--optional", nargs="+", help="Optional variables")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Interactive configuration dashboard")
    dashboard_parser.add_argument("--env", help="Environment name")
    dashboard_parser.add_argument("--path", default=".env", help="Path to .env file")
    dashboard_parser.add_argument("--trace", action="store_true", help="Show variable origins")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "show":
            cmd_show(args)
        elif args.command == "export":
            cmd_export(args)
        elif args.command == "validate":
            cmd_validate(args)
        elif args.command == "generate-example":
            cmd_generate_example(args)
        elif args.command == "dashboard":
            cmd_dashboard(args)
        elif args.command == "audit":
            cmd_audit(args)
        elif args.command == "explain":
            cmd_explain(args)
        elif args.command == "diff":
            cmd_diff(args)
        elif args.command == "encrypt":
            cmd_encrypt(args)
        elif args.command == "decrypt":
            cmd_decrypt(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_show(args):
    from .core.loader import load_env
    
    config = load_env(
        path=args.path,
        env=args.env,
        mask_secrets=not args.unmask
    )
    
    if args.format == "json":
        print(json.dumps(config.safe_repr(), indent=2))
    elif args.format == "yaml":
        try:
            import yaml
            print(yaml.dump(config.safe_repr(), default_flow_style=False))
        except ImportError:
            print("PyYAML is required for YAML output. Install with: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
    else:  # pretty
        from .utils import pretty_print_config
        pretty_print_config(config, mask=not args.unmask)

def cmd_export(args):
    from .core.loader import load_env
    
    config = load_env(
        path=args.path,
        env=args.env
    )
    
    config.save(args.output, format=args.format)
    print(f"Config exported to {args.output}")

def cmd_validate(args):
    """Validate environment configuration (CI-safe)."""
    from .core.loader import load_env
    from .exceptions import EnvLoaderError, ValidationError
    
    # CI mode: no providers, strict validation
    providers = [] if args.ci else None
    failure_policy = {} if args.ci else None
    
    try:
        result = load_env(
            path=args.path,
            env=args.env,
            required=args.required or [],
            strict=args.strict or args.ci,
            providers=providers,
            failure_policy=failure_policy,
        )
        
        # Handle tuple return (config, audit) if audit enabled
        if isinstance(result, tuple):
            config, _ = result
        else:
            config = result
        
        print("✓ Validation passed")
        print(f"Found {len(config)} environment variables")
        
        if args.ci:
            print("✓ CI mode: No cloud providers accessed")
        
        sys.exit(0)
    except (EnvLoaderError, ValidationError) as e:
        print(f"✗ Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_generate_example(args):
    from .exporters import generate_env_example
    
    generate_env_example(
        required=args.required or [],
        optional=args.optional or [],
        defaults={},
        types={},
        output_path=args.output
    )
    print(f"Generated {args.output}")

def cmd_dashboard(args):
    """Interactive configuration dashboard."""
    from .core.loader import load_env
    
    config = load_env(
        path=args.path,
        env=args.env,
        trace=args.trace
    )
    
    print("=" * 70)
    print("ENV-LOADER-PRO DASHBOARD")
    print("=" * 70)
    print()
    
    # Summary
    print(f"📊 Configuration Summary")
    print(f"   Total variables: {len(config)}")
    print(f"   Environment: {args.env or 'default'}")
    print(f"   Path: {args.path}")
    print()
    
    # List variables
    print("📋 Environment Variables:")
    print("-" * 70)
    
    safe_config = config.safe_repr()
    for key in sorted(safe_config.keys()):
        value = safe_config[key]
        value_str = str(value)
        if len(value_str) > 50:
            value_str = value_str[:47] + "..."
        
        # Show origin if tracing enabled
        origin_info = ""
        if args.trace and hasattr(config, 'trace'):
            origin = config.trace(key)
            origin_info = f" [{origin}]"
        
        print(f"  {key:30} = {value_str:30}{origin_info}")
    
    print()
    
    # Validation status
    print("✓ Validation: PASSED")
    print()
    
    # Export options
    print("💾 Export Options:")
    print("   - JSON: envloader export --output config.json --format json")
    print("   - YAML: envloader export --output config.yaml --format yaml")
    print()
    
    # Trace info
    if args.trace and hasattr(config, 'get_origins'):
        origins = config.get_origins()
        origin_summary = {}
        for key, origin in origins.items():
            origin_summary[origin] = origin_summary.get(origin, 0) + 1
        
        print("📍 Variable Origins:")
        for origin, count in sorted(origin_summary.items()):
            print(f"   {origin:20} : {count} variables")
        print()

def cmd_audit(args):
    """Show configuration audit trail."""
    from .core.loader import load_env
    
    # CI mode: no providers
    providers = [] if args.ci else None
    
    result = load_env(
        path=args.path,
        env=args.env,
        audit=True,
        providers=providers,
    )
    
    # Handle tuple return
    if isinstance(result, tuple):
        config, audit = result
    else:
        # Should not happen if audit=True, but handle gracefully
        print("Error: Audit not available", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        print(audit.to_json())
    else:
        print("=== Configuration Audit ===")
        print()
        summary = audit.get_summary()
        print(f"Total variables: {summary['total_variables']}")
        print(f"Masked variables: {summary['masked_variables']}")
        print()
        print("Sources:")
        for source, count in sorted(summary['sources'].items()):
            print(f"  {source:20} : {count} variables")
        if summary['providers']:
            print()
            print("Providers:")
            for provider, count in sorted(summary['providers'].items()):
                print(f"  {provider:20} : {count} variables")
        print()
        print("Detailed entries:")
        for key, entry in sorted(audit.entries.items()):
            provider_str = f" ({entry.provider})" if entry.provider else ""
            masked_str = " [MASKED]" if entry.masked else ""
            print(f"  {key:30} : {entry.source}{provider_str}{masked_str}")

def cmd_explain(args):
    """Explain configuration precedence and policies."""
    from .core.policy import create_default_policies
    from .settings import SOURCE_PRIORITY
    
    if args.format == "json":
        output = {
            "precedence": [
                {"priority": 1, "source": "cloud_providers", "description": "Azure Key Vault, AWS Secrets Manager"},
                {"priority": 2, "source": "system", "description": "System environment variables"},
                {"priority": 3, "source": "docker_k8s", "description": "Docker/K8s mounted secrets"},
                {"priority": 4, "source": "env_specific", "description": f".env.{args.env or 'ENV'} file"},
                {"priority": 5, "source": "base_file", "description": "Base .env file"},
                {"priority": 6, "source": "schema_defaults", "description": "Schema default values"},
            ],
            "failure_policies": create_default_policies(),
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 70)
        print("CONFIGURATION PRECEDENCE & POLICIES")
        print("=" * 70)
        print()
        print("Resolution Order (highest to lowest priority):")
        print()
        
        precedence = [
            (1, "cloud_providers", "Cloud providers (Azure Key Vault, AWS Secrets Manager)"),
            (2, "system", "System environment variables"),
            (3, "docker_k8s", "Docker/K8s mounted secrets"),
            (4, "env_specific", f".env.{args.env or 'ENV'} (environment-specific file)"),
            (5, "base_file", "Base .env file"),
            (6, "schema_defaults", "Schema default values"),
        ]
        
        for priority, source, description in precedence:
            print(f"  {priority}. {description}")
            print(f"     Source: {source}")
            print()
        
        print("Failure Policies (default):")
        print()
        policies = create_default_policies()
        for provider, policy in sorted(policies.items()):
            policy_desc = {
                "fail": "Raise error on failure",
                "warn": "Log warning and continue",
                "fallback": "Silently continue (use fallback)",
            }.get(policy, policy)
            print(f"  {provider:20} : {policy:10} ({policy_desc})")
        print()
        print("Note: Later sources override earlier ones in case of conflicts.")
        print("      Cloud providers have highest priority (secrets win).")

def cmd_diff(args):
    """Compare configuration changes."""
    from .core.diff import diff_configs
    from .core.loader import load_env
    from .exceptions import EnvLoaderError
    
    # CI mode: no providers
    providers = [] if args.ci else None
    
    try:
        current = load_env(
            path=args.path,
            env=args.env,
            providers=providers,
        )
        
        # Handle tuple return
        if isinstance(current, tuple):
            current, _ = current
        
        if args.baseline:
            # Load baseline for comparison
            baseline = load_env(
                path=args.baseline,
                providers=providers,
            )
            if isinstance(baseline, tuple):
                baseline, _ = baseline
        else:
            # No baseline - just show current
            baseline = {}
        
        # Compute diff
        diff = diff_configs(current, baseline)
        
        # Check for secret changes if requested
        if args.deny_secret_changes:
            try:
                diff.validate_no_secret_changes()
            except ValueError as e:
                print(f"✗ {e}", file=sys.stderr)
                sys.exit(1)
        
        # Print diff
        if not diff.has_changes():
            print("✓ No changes detected")
            sys.exit(0)
        
        print("Configuration Changes:")
        print()
        if diff.added:
            print("Added variables:")
            for key in sorted(diff.added):
                print(f"  + {key}")
            print()
        if diff.removed:
            print("Removed variables:")
            for key in sorted(diff.removed):
                print(f"  - {key}")
            print()
        if diff.changed:
            print("Changed variables:")
            for key in sorted(diff.changed):
                print(f"  ~ {key}")
            print()
        
        sys.exit(0)
    except EnvLoaderError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_encrypt(args):
    """Encrypt a .env file."""
    from .crypto import encrypt_file
    from .exceptions import DecryptionError
    
    try:
        encrypt_file(
            input_path=args.input,
            output_path=args.output,
            method=args.method,
            key_path=args.key,
        )
        output = args.output or f"{args.input}.enc"
        print(f"✓ Encrypted {args.input} to {output}")
    except DecryptionError as e:
        print(f"✗ Encryption failed: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_decrypt(args):
    """Decrypt an encrypted .env file."""
    from .crypto import decrypt_file
    from .exceptions import DecryptionError
    
    try:
        decrypt_file(
            input_path=args.input,
            output_path=args.output,
            key_path=args.key,
        )
        output = args.output or (args.input[:-4] if args.input.endswith(".enc") else f"{args.input}.decrypted")
        print(f"✓ Decrypted {args.input} to {output}")
    except DecryptionError as e:
        print(f"✗ Decryption failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

