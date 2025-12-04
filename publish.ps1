# PowerShell script to publish env-loader-pro to PyPI
# Usage: .\publish.ps1 <version>
# Example: .\publish.ps1 0.2.0
#
# IMPORTANT: Make sure you've committed to GitHub first!
# git add . && git commit -m "Release v$Version" && git push origin main
# git tag -a v$Version -m "Release v$Version" && git push origin v$Version

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Publishing env-loader-pro v$Version" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  Make sure you've:" -ForegroundColor Yellow
Write-Host "   1. Committed changes to GitHub" -ForegroundColor Yellow
Write-Host "   2. Created and pushed git tag v$Version" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Red
    exit 0
}
Write-Host ""

# Update version in pyproject.toml
Write-Host "Updating version in pyproject.toml..." -ForegroundColor Yellow
$pyproject = Get-Content pyproject.toml -Raw
$pyproject = $pyproject -replace 'version = "[\d.]+"', "version = `"$Version`""
Set-Content pyproject.toml -Value $pyproject

# Update version in __init__.py
Write-Host "Updating version in __init__.py..." -ForegroundColor Yellow
$init = Get-Content src\env_loader_pro\__init__.py -Raw
$init = $init -replace '__version__ = "[\d.]+"', "__version__ = `"$Version`""
Set-Content src\env_loader_pro\__init__.py -Value $init

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Build
Write-Host "Building package..." -ForegroundColor Yellow
python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Check
Write-Host "Checking package..." -ForegroundColor Yellow
twine check dist/*
if ($LASTEXITCODE -ne 0) {
    Write-Host "Package check failed!" -ForegroundColor Red
    exit 1
}

# Upload
Write-Host "Uploading to PyPI..." -ForegroundColor Yellow
Write-Host "You will be prompted for your PyPI credentials." -ForegroundColor Cyan
twine upload dist/*

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSuccessfully published version $Version to PyPI!" -ForegroundColor Green
    Write-Host "Install with: pip install env-loader-pro==$Version" -ForegroundColor Cyan
} else {
    Write-Host "Upload failed!" -ForegroundColor Red
    exit 1
}

