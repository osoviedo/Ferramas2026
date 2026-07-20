# Ferramas - flujo demo Mercado Pago con ngrok
# Uso: .\scripts\demo_pago_mp.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Port = 5000

function Find-Ngrok {
    $candidates = @(
        (Join-Path $ProjectRoot "tools\ngrok.exe"),
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ngrok.exe",
        "C:\Program Files\ngrok\ngrok.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }
    $cmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notmatch "npm") { return $cmd.Source }
    return $null
}

function Test-FlaskRunning {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -TimeoutSec 3 -UseBasicParsing
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Get-NgrokPublicUrl {
    Start-Sleep -Seconds 2
    try {
        $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5
        $https = $tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
        if ($https) { return $https.public_url.TrimEnd("/") }
    } catch {
        return $null
    }
    return $null
}

Write-Host ""
Write-Host "=== Ferramas: demo pago Mercado Pago (ngrok) ===" -ForegroundColor Cyan
Write-Host ""

$ngrok = Find-Ngrok
if (-not $ngrok) {
    Write-Host "[MANUAL] Instala ngrok v3:" -ForegroundColor Yellow
    Write-Host "  winget install Ngrok.Ngrok --source winget"
    Write-Host "  O descarga desde https://ngrok.com/download"
    Write-Host "  O copia ngrok.exe en: $ProjectRoot\tools\ngrok.exe"
    exit 1
}

Write-Host "ngrok encontrado: $ngrok" -ForegroundColor Green
& $ngrok version 2>&1 | ForEach-Object { Write-Host "  $_" }

if (-not (Test-FlaskRunning)) {
    Write-Host ""
    Write-Host "[MANUAL] Flask no responde en http://127.0.0.1:$Port" -ForegroundColor Yellow
    Write-Host "  Abre otra terminal y ejecuta:"
    Write-Host "  cd $ProjectRoot"
    Write-Host "  .\venv\Scripts\Activate.ps1"
    Write-Host "  python run.py"
    Write-Host ""
    Write-Host "  Luego vuelve a ejecutar este script."
    exit 1
}

Write-Host "Flask OK en puerto $Port" -ForegroundColor Green

$existing = Get-NgrokPublicUrl
if ($existing) {
    Write-Host ""
    Write-Host "Tunel ngrok ya activo: $existing" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Iniciando ngrok http $Port ..." -ForegroundColor Cyan
    Write-Host "Si es la primera vez, configura authtoken (ver pasos abajo)" -ForegroundColor DarkGray
    Start-Process -FilePath $ngrok -ArgumentList @("http", "$Port") -WindowStyle Normal
    $existing = $null
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 2
        $existing = Get-NgrokPublicUrl
        if ($existing) { break }
    }
}

if (-not $existing) {
    Write-Host ""
    Write-Host "[MANUAL] ngrok no levanto el tunel. Pasos:" -ForegroundColor Yellow
    Write-Host "  1. Crea cuenta: https://dashboard.ngrok.com/signup"
    Write-Host "  2. Copia authtoken: https://dashboard.ngrok.com/get-started/your-authtoken"
    Write-Host "  3. ngrok config add-authtoken TU_TOKEN"
    Write-Host "  4. ngrok http 5000"
    Write-Host "  5. Vuelve a correr este script"
    exit 1
}

Write-Host ""
Write-Host "URL publica HTTPS:" -ForegroundColor Green
Write-Host "  $existing" -ForegroundColor White
Write-Host ""
Write-Host "[MANUAL] Edita .env:" -ForegroundColor Yellow
Write-Host "  PUBLIC_BASE_URL=$existing" -ForegroundColor White
Write-Host ""
Write-Host "[MANUAL] Reinicia Flask (Ctrl+C y python run.py)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Prueba de pago:" -ForegroundColor Cyan
Write-Host "  1. Abre la URL ngrok (no 127.0.0.1)"
Write-Host "  2. Carrito -> Checkout -> Mercado Pago"
Write-Host "  3. Sandbox: TESTUSER o tarjeta APRO, CVV 123"
Write-Host "  4. Al volver, pedido en estado aprobado"
Write-Host ""
Write-Host "Panel ngrok: http://127.0.0.1:4040" -ForegroundColor DarkGray
Write-Host ""
