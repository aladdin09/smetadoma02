# Обновление репозитория (git pull)
# Запускать из корня репозитория или указать путь в $RepoPath

param(
    [string]$RepoPath = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
    Write-Host "Ошибка: в '$RepoPath' не найден репозиторий Git (.git)." -ForegroundColor Red
    Write-Host "Укажите путь к репозиторию: .\update_repo.ps1 -RepoPath 'D:\Projects\YourRepo'" -ForegroundColor Yellow
    exit 1
}

Push-Location $RepoPath
try {
    Write-Host "Обновление репозитория: $RepoPath" -ForegroundColor Cyan
    git fetch --all
    git pull
    Write-Host "Готово." -ForegroundColor Green
} finally {
    Pop-Location
}
