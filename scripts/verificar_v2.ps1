# =============================================================================
# verificar_v2.ps1 — reproduce los 12 probes no destructivos contra la V2
# (https://localhost). Equivalente Windows de scripts/verificar_v2.sh.
#
# Uso:
#   .\scripts\verificar_v2.ps1 [-BaseUrl https://localhost] [-Brute $false]
#
# Notas:
#   - No escribe datos: CSRF/405/403 detienen la request antes de tocar la BD.
#   - Requiere la V2 desplegada (docker compose up -d) y curl.exe.
#   - El probe 12 (fuerza bruta) solo corre con -Brute $true porque el
#     rate-limit es por IP y bloquea /login ~1 min para todos.
# =============================================================================
param(
    [string]$BaseUrl = "https://localhost",
    [switch]$Brute
)

$PASS = 0; $FAIL = 0
$CJ = Join-Path $env:TEMP "v2_admin.txt"
$CJD = Join-Path $env:TEMP "v2_doc.txt"
$Payload = Join-Path $env:TEMP "payload_v2.html"
Remove-Item $CJ, $CJD, $Payload -ErrorAction SilentlyContinue

function Check([string]$Name, [string]$Regex, [string]$Actual) {
    if ($Actual -match $Regex) { Write-Host "OK   $Name ($Actual)"; $script:PASS++ }
    else { Write-Host "FAIL $Name (esperado ~$Regex, actual: $Actual)"; $script:FAIL++ }
}

function Get-Token([string]$Url, [string]$Jar) {
    $html = (& curl.exe -ks -b $Jar -c $Jar $Url) -join "`n"
    if ($html -match 'name="csrf_token" value="([^"]+)"') { $Matches[1] }
}

Write-Host "== V2 verificacion: $BaseUrl =="

# 1. TLS
$R = & curl.exe -s -o NUL -w "%{http_code}->%{redirect_url}" http://localhost/
Check "1 HTTP->HTTPS (301)" "^301" $R
$R = & curl.exe -k -s -o NUL -w "%{http_code}" "$BaseUrl/"
Check "1b HTTPS responde (302)" "^302" $R

# 2. Headers de seguridad
$H = (& curl.exe -k -s -D - -o NUL "$BaseUrl/") -join "`n"
foreach ($h in @("strict-transport-security", "content-security-policy", "x-frame-options", "x-content-type-options")) {
    if ($H -match $h) { Write-Host "OK   2 header $h"; $script:PASS++ }
    else { Write-Host "FAIL 2 header $h"; $script:FAIL++ }
}

# 3. SQLi en login: sin bypass (200)
$Tok = Get-Token "$BaseUrl/login" $CJ
$R = & curl.exe -k -s -b $CJ -c $CJ -o NUL -w "%{http_code}" -X POST "$BaseUrl/login" `
     --data-urlencode "username=admin' OR '1'='1' --" --data-urlencode "password=x" `
     --data-urlencode "csrf_token=$Tok"
Check "3 SQLi login sin bypass (200)" "^200" $R

# Login admin real
$Tok = Get-Token "$BaseUrl/login" $CJ
& curl.exe -k -s -b $CJ -c $CJ -o NUL -X POST "$BaseUrl/login" `
     --data-urlencode "username=admin" --data-urlencode "password=admin123" `
     --data-urlencode "csrf_token=$Tok" | Out-Null

# 4. CSRF: POST sin token -> 400
$R = & curl.exe -k -s -b $CJ -c $CJ -o NUL -w "%{http_code}" -X POST "$BaseUrl/estudiantes/crear" `
     --data-urlencode "nombre=HACK" --data-urlencode "email=hack@x.com" --data-urlencode "carrera=X"
Check "4 CSRF sin token (400)" "^400" $R

# 5. Delete por GET -> 405
$R = & curl.exe -k -s -b $CJ -c $CJ -o NUL -w "%{http_code}" "$BaseUrl/estudiantes/eliminar/1"
Check "5 GET delete (405)" "^405" $R

# 6. 404 personalizado
$R = & curl.exe -k -s -b $CJ -c $CJ -o NUL -w "%{http_code}" "$BaseUrl/no-existe-xyz"
Check "6 404 personalizado" "^404" $R

# 7. RCE bloqueado
$Tok = Get-Token "$BaseUrl/diagnostico" $CJ
$Body = (& curl.exe -k -s -b $CJ -c $CJ -X POST "$BaseUrl/diagnostico" `
     --data-urlencode "comando=whoami" --data-urlencode "csrf_token=$Tok") -join "`n"
if ($Body -match "no permitido") { Write-Host "OK   7 RCE bloqueado (mensaje)"; $script:PASS++ } else { Write-Host "FAIL 7 RCE bloqueado"; $script:FAIL++ }

# 8. SSRF -> 403
foreach ($u in @("http://169.254.169.254/latest/meta-data/", "http://localhost/", "http://192.168.1.1/")) {
    $Tok = Get-Token "$BaseUrl/importar" $CJ
    $R = & curl.exe -k -s -b $CJ -c $CJ -o NUL -w "%{http_code}" -X POST "$BaseUrl/importar" `
         --data-urlencode "url=$u" --data-urlencode "csrf_token=$Tok"
    $nom = $u -replace 'http://', ''
    Check "8 SSRF $nom (403)" "^403" $R
}

# 9. SQLi UNION sin fuga
$Body = (& curl.exe -k -s -b $CJ -c $CJ --get `
     --data-urlencode "buscar=x' UNION SELECT username,password,rol,'x' FROM usuarios --" `
     "$BaseUrl/estudiantes") -join "`n"
$hashes = ([regex]::Matches($Body, '2b\$12')).Count
if ($hashes -eq 0) { Write-Host "OK   9 UNION sin fuga (0 hashes)"; $script:PASS++ } else { Write-Host "FAIL 9 UNION ($hashes hashes)"; $script:FAIL++ }

# 10. Upload .html malicioso -> rechazado
Set-Content -Path $Payload -Value '<script>alert(1)</script>'
$Tok = Get-Token "$BaseUrl/archivos" $CJ
$Body = (& curl.exe -k -s -b $CJ -c $CJ -L -F "archivo=@$Payload;type=text/html" `
     -F "csrf_token=$Tok" "$BaseUrl/archivos/subir") -join "`n"
if ($Body -match "no permitido") { Write-Host "OK   10 upload html bloqueado"; $script:PASS++ } else { Write-Host "FAIL 10 upload html"; $script:FAIL++ }

# 11. RBAC docente -> 403
$Tok = Get-Token "$BaseUrl/login" $CJD
& curl.exe -k -s -b $CJD -c $CJD -o NUL -X POST "$BaseUrl/login" `
     --data-urlencode "username=profesor" --data-urlencode "password=profesor" `
     --data-urlencode "csrf_token=$Tok" | Out-Null
foreach ($p in @("/importar", "/diagnostico")) {
    $R = & curl.exe -k -s -b $CJD -c $CJD -o NUL -w "%{http_code}" "$BaseUrl$p"
    Check "11 docente $p (403)" "^403" $R
}

# 12. Fuerza bruta (opcional)
if ($Brute) {
    $CJB = Join-Path $env:TEMP "v2_bf.txt"
    for ($i = 1; $i -le 6; $i++) {
        $Tok = Get-Token "$BaseUrl/login" $CJB
        $R = & curl.exe -k -s -b $CJB -c $CJB -o NUL -w "%{http_code}" -X POST "$BaseUrl/login" `
             --data-urlencode "username=fuerzabruta" --data-urlencode "password=wrong" `
             --data-urlencode "csrf_token=$Tok"
        Write-Host "    intento $i -> $R"
    }
    Check "12 brute force (429)" "^429" $R
    Write-Host "  -> rate-limit activo ~1 min por IP; 'docker compose restart v2' lo limpia"
} else {
    Write-Host "OK   12 brute force omitido (ejecutar con -Brute)"
}

Write-Host ""
Write-Host "== RESUMEN: PASS=$PASS FAIL=$FAIL =="
if ($FAIL -gt 0) { exit 1 }
