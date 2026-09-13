param(
    [string]$Source = (Split-Path -Parent $MyInvocation.MyCommand.Path),
    [switch]$Uninstall
)
$ErrorActionPreference = "Stop"
$appName = "Orville Signal Room"
$installRoot = Join-Path $env:LOCALAPPDATA "Programs\Orville"
$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Orville Signal Room.lnk"
if ($Uninstall) {
    Remove-Item -Recurse -Force $installRoot -ErrorAction SilentlyContinue
    Remove-Item -Force $shortcutPath -ErrorAction SilentlyContinue
    Write-Output "Removed $appName program files. User data remains in $env:LOCALAPPDATA\Orville."
    exit 0
}
$exe = Join-Path $Source "Orville-Signal-Room.exe"
if (-not (Test-Path $exe)) { throw "Orville-Signal-Room.exe was not found in $Source" }
New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
Copy-Item -Recurse -Force (Join-Path $Source "*") $installRoot
$target = Join-Path $installRoot "Orville-Signal-Room.exe"
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($shortcutPath)
$link.TargetPath = $target
$link.WorkingDirectory = $installRoot
$link.Description = "Orville autonomous Signal Room"
$link.Save()
Write-Output "Installed to $installRoot"
Write-Output "Desktop shortcut: $shortcutPath"
Write-Output "User data remains in $env:LOCALAPPDATA\Orville"
