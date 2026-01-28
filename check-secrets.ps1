# Pre-Push Security Check Script
# Run this before every git push to ensure no secrets are exposed

Write-Host "Running Security Check..." -ForegroundColor Cyan
Write-Host ""

# Check 1: Verify .env files are ignored
Write-Host "Checking .env files..." -ForegroundColor Yellow
$envFiles = @(
    "backend_agents/.env",
    "client/.env"
)

$allIgnored = $true
foreach ($file in $envFiles) {
    if (Test-Path $file) {
        $ignored = git check-ignore $file 2>$null
        if ($ignored) {
            Write-Host "  OK: $file is ignored" -ForegroundColor Green
        } else {
            Write-Host "  ERROR: $file is NOT ignored!" -ForegroundColor Red
            $allIgnored = $false
        }
    }
}

# Check 2: Verify Firebase JSON is ignored
Write-Host ""
Write-Host "Checking Firebase service account..." -ForegroundColor Yellow
$firebaseJson = "backend_agents/datacue-50971-firebase-adminsdk-fbsvc-6903fdc3d2.json"
if (Test-Path $firebaseJson) {
    $ignored = git check-ignore $firebaseJson 2>$null
    if ($ignored) {
        Write-Host "  OK: Firebase JSON is ignored" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: Firebase JSON is NOT ignored!" -ForegroundColor Red
        $allIgnored = $false
    }
}

# Check 3: Search for exposed secrets in staged files
Write-Host ""
Write-Host "Scanning staged files for secrets..." -ForegroundColor Yellow
$secrets = @("api_key", "password", "secret", "private_key")
$foundSecrets = $false

foreach ($secret in $secrets) {
    $results = git diff --cached | Select-String -Pattern $secret -CaseSensitive:$false
    if ($results) {
        Write-Host "  WARNING: Found $secret in staged changes" -ForegroundColor Red
        $foundSecrets = $true
    }
}

if (-not $foundSecrets) {
    Write-Host "  OK: No secrets found in staged files" -ForegroundColor Green
}

# Check 4: List what will be committed
Write-Host ""
Write-Host "Files to be committed:" -ForegroundColor Yellow
git diff --cached --name-only | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }

# Final verdict
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allIgnored -and -not $foundSecrets) {
    Write-Host "RESULT: SAFE TO PUSH" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run: git push origin main" -ForegroundColor Cyan
} else {
    Write-Host "RESULT: NOT SAFE TO PUSH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Action required:" -ForegroundColor Yellow
    Write-Host "1. Fix .gitignore" -ForegroundColor White
    Write-Host "2. Remove secrets from staged files" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
}
Write-Host "========================================" -ForegroundColor Cyan
