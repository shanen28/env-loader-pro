"""Manual testing script for env-loader-pro.
Run this after installing the package to verify all features work.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path for development testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_loading():
    """Test basic environment loading."""
    print("=" * 60)
    print("Test 1: Basic Loading")
    print("=" * 60)
    
    from env_loader_pro import load_env
    
    # Create temporary .env file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("PORT=8080\n")
        f.write("DEBUG=true\n")
        f.write("API_KEY=secret12345\n")
        env_path = f.name
    
    try:
        config = load_env(
            path=env_path,
            types={"PORT": int, "DEBUG": bool},
            required=["API_KEY"]
        )
        
        print(f"✓ PORT: {config['PORT']} (type: {type(config['PORT']).__name__})")
        print(f"✓ DEBUG: {config['DEBUG']} (type: {type(config['DEBUG']).__name__})")
        print(f"✓ API_KEY: {config['API_KEY']}")
        print("✓ Basic loading works!")
    finally:
        os.unlink(env_path)

def test_variable_expansion():
    """Test variable expansion."""
    print("\n" + "=" * 60)
    print("Test 2: Variable Expansion")
    print("=" * 60)
    
    from env_loader_pro import load_env
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("BASE_URL=https://example.com\n")
        f.write("API_ENDPOINT=${BASE_URL}/api\n")
        f.write("FULL_URL=${API_ENDPOINT}/v1\n")
        env_path = f.name
    
    try:
        config = load_env(path=env_path)
        print(f"✓ BASE_URL: {config['BASE_URL']}")
        print(f"✓ API_ENDPOINT: {config['API_ENDPOINT']}")
        print(f"✓ FULL_URL: {config['FULL_URL']}")
        assert config['API_ENDPOINT'] == "https://example.com/api"
        assert config['FULL_URL'] == "https://example.com/api/v1"
        print("✓ Variable expansion works!")
    finally:
        os.unlink(env_path)

def test_list_parsing():
    """Test list parsing."""
    print("\n" + "=" * 60)
    print("Test 3: List Parsing")
    print("=" * 60)
    
    from env_loader_pro import load_env
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('DOMAINS=["a.com","b.com","c.com"]\n')
        f.write("LIMITS=10,20,400\n")
        env_path = f.name
    
    try:
        config = load_env(path=env_path, types={"DOMAINS": list, "LIMITS": list})
        print(f"✓ DOMAINS (JSON): {config['DOMAINS']}")
        print(f"✓ LIMITS (CSV): {config['LIMITS']}")
        assert isinstance(config['DOMAINS'], list)
        assert isinstance(config['LIMITS'], list)
        print("✓ List parsing works!")
    finally:
        os.unlink(env_path)

def test_validation_rules():
    """Test validation rules."""
    print("\n" + "=" * 60)
    print("Test 4: Validation Rules")
    print("=" * 60)
    
    from env_loader_pro import load_env
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("PORT=8080\n")
        env_path = f.name
    
    try:
        config = load_env(
            path=env_path,
            types={"PORT": int},
            rules={"PORT": lambda v: 1024 < v < 65535}
        )
        print(f"✓ PORT validated: {config['PORT']}")
        print("✓ Validation rules work!")
    finally:
        os.unlink(env_path)

def test_safe_repr():
    """Test safe representation."""
    print("\n" + "=" * 60)
    print("Test 5: Safe Representation (Secret Masking)")
    print("=" * 60)
    
    from env_loader_pro import load_env
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("API_KEY=secret12345\n")
        f.write("PORT=8080\n")
        env_path = f.name
    
    try:
        config = load_env(path=env_path, types={"PORT": int})
        safe = config.safe_repr()
        print(f"✓ Original API_KEY: {config['API_KEY']}")
        print(f"✓ Masked API_KEY: {safe['API_KEY']}")
        print(f"✓ PORT (not masked): {safe['PORT']}")
        assert safe['API_KEY'] != config['API_KEY']
        assert "****" in safe['API_KEY'] or safe['API_KEY'] == "************"
        print("✓ Secret masking works!")
    finally:
        os.unlink(env_path)

def test_export():
    """Test config export."""
    print("\n" + "=" * 60)
    print("Test 6: Config Export")
    print("=" * 60)
    
    import tempfile
    from env_loader_pro import load_env
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("PORT=8080\n")
        f.write("API_KEY=secret123\n")
        env_path = f.name
    
    try:
        config = load_env(path=env_path, types={"PORT": int})
        
        # Export to JSON
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as out:
            output_path = out.name
        
        config.save(output_path, format="json")
        print(f"✓ Config exported to {output_path}")
        
        # Verify file exists and has content
        assert os.path.exists(output_path)
        import json
        with open(output_path) as f:
            data = json.load(f)
            assert "PORT" in data
        print("✓ Export to JSON works!")
        
        os.unlink(output_path)
    finally:
        os.unlink(env_path)

def test_dataclass_schema():
    """Test dataclass schema support."""
    print("\n" + "=" * 60)
    print("Test 7: Dataclass Schema")
    print("=" * 60)
    
    from dataclasses import dataclass
    from env_loader_pro import load_with_schema
    
    @dataclass
    class Config:
        port: int
        debug: bool
        api_key: str
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("PORT=8080\n")
        f.write("DEBUG=true\n")
        f.write("API_KEY=secret123\n")
        env_path = f.name
    
    try:
        config = load_with_schema(Config, path=env_path)
        print(f"✓ Config.port: {config.port}")
        print(f"✓ Config.debug: {config.debug}")
        print(f"✓ Config.api_key: {config.api_key}")
        assert config.port == 8080
        assert config.debug is True
        print("✓ Dataclass schema works!")
    finally:
        os.unlink(env_path)

def test_generate_example():
    """Test .env.example generation."""
    print("\n" + "=" * 60)
    print("Test 8: Generate .env.example")
    print("=" * 60)
    
    from env_loader_pro import generate_env_example
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.example', delete=False) as f:
        output_path = f.name
    
    try:
        generate_env_example(
            required=["API_KEY", "DB_URI"],
            optional=["DEBUG"],
            defaults={"PORT": 8080, "DEBUG": False},
            types={"PORT": int, "DEBUG": bool},
            output_path=output_path
        )
        
        assert os.path.exists(output_path)
        content = Path(output_path).read_text()
        print("✓ Generated .env.example:")
        print(content[:200] + "..." if len(content) > 200 else content)
        assert "API_KEY" in content
        assert "PORT=8080" in content
        print("✓ .env.example generation works!")
        
        os.unlink(output_path)
    except Exception as e:
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise

def main():
    """Run all manual tests."""
    print("\n" + "=" * 60)
    print("ENV-LOADER-PRO MANUAL TEST SUITE")
    print("=" * 60)
    print("\nRunning manual tests...\n")
    
    tests = [
        test_basic_loading,
        test_variable_expansion,
        test_list_parsing,
        test_validation_rules,
        test_safe_repr,
        test_export,
        test_dataclass_schema,
        test_generate_example,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✓ Passed: {passed}")
    if failed > 0:
        print(f"✗ Failed: {failed}")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())

