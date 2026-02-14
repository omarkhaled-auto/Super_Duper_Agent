$dirs = Get-ChildItem -Path "C:\Users\Omar Khaled\OneDrive\Desktop" -Directory -Recurse -Filter "node_modules" -Depth 3 -ErrorAction SilentlyContinue | Where-Object { $_.Parent.Name -ne "node_modules" }
foreach ($d in $dirs) {
    $proj = $d.Parent.FullName
    $has = (Test-Path (Join-Path $proj "package-lock.json")) -or (Test-Path (Join-Path $proj "pnpm-lock.yaml")) -or (Test-Path (Join-Path $proj "yarn.lock"))
    if (-not $has) {
        Write-Output "NO LOCK: $proj"
    }
}
Write-Output "DONE"
