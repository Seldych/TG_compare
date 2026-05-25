$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path -Path $scriptDir -ChildPath "text_comparer.py"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path -Path $desktopPath -ChildPath "Сравнение файлов.lnk"

# Find pythonw executable
$py = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if (-not $py) {
    $py = Get-Command python.exe -ErrorAction SilentlyContinue
}
if (-not $py) {
    Write-Error "Python не найден. Установите Python и добавьте его в PATH."
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $py.Source
$shortcut.Arguments = "`"$scriptPath`""
$shortcut.WorkingDirectory = $scriptDir
$shortcut.Description = "Сравнение текстовых файлов"
$shortcut.Save()

Write-Host "Ярлык создан на рабочем столе: $shortcutPath" -ForegroundColor Green
Write-Host "Цель: $($py.Source) `"$scriptPath`"" -ForegroundColor Gray
