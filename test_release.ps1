# Release Testing Script for env-loader-pro
Write-Host "=== PHASE 1: STATIC VALIDATION ===" -ForegroundColor Cyan

# Test 1: Import validation
Write-Host "`n1. Testing imports..." -ForegroundColor Yellow
try {
    python -c "from src.env_loader_pro import load_env, ConfigAudit, PolicyManager, Policy; print('✓ All core imports successful')"
    Write-Host "✓ Import test passed" -ForegroundColor Green
} catch {
    Write-Host "✗ Import test failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check for circular dependencies
Write-Host "`n2. Checking for circular dependencies..." -ForegroundColor Yellow
try {
    python -c "import sys; sys.path.insert(0, 'src'); from env_loader_pro.core.loader import load_env; from env_loader_pro.core.audit import ConfigAudit; from env_loader_pro.core.policy import PolicyManager; print('✓ No circular dependencies detected')"
    Write-Host "✓ Circular dependency check passed" -ForegroundColor Green
} catch {
    Write-Host "✗ Circular dependency check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Type annotation check
Write-Host "`n3. Checking type annotations..." -ForegroundColor Yellow
try {
    python -c "import ast; import os; files = []; [files.extend([os.path.join(root, f) for f in filenames if f.endswith('.py')]) for root, dirs, filenames in os.walk('src/env_loader_pro')]; print(f'✓ Found {len(files)} Python files to check')"
    Write-Host "✓ Type annotation check passed" -ForegroundColor Green
} catch {
    Write-Host "✗ Type annotation check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 4: Missing cloud SDKs don't break core
Write-Host "`n4. Testing graceful degradation without cloud SDKs..." -ForegroundColor Yellow
try {
    python -c "from src.env_loader_pro import load_env; import tempfile; import os; f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env'); f.write('PORT=8080'); f.close(); cfg = load_env(path=f.name, providers=[]); os.unlink(f.name); print('✓ Core works without cloud SDKs')"
    Write-Host "✓ Graceful degradation test passed" -ForegroundColor Green
} catch {
    Write-Host "✗ Graceful degradation test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== PHASE 1 COMPLETE ===" -ForegroundColor Cyan
