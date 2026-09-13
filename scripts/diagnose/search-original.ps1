$roots = @(
  'C:\Users\Zeref\Documents\Manus Projects',
  'C:\Users\Zeref\Downloads',
  'C:\Users\Zeref\Desktop'
)
foreach ($root in $roots) {
  if (Test-Path $root) {
    Write-Output "=== $root ==="
    Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue | Select-Object -First 100 FullName
    Get-ChildItem -LiteralPath $root -Recurse -Force -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -match '(?i)orville|gui|frontend|desktop|electron|tauri' -or $_.Extension -in @('.html','.jsx','.tsx','.vue','.qml','.ui','.fig','.sketch') } |
      Select-Object -First 300 FullName,Length,LastWriteTime
  }
}
