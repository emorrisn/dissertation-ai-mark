# Check for administrative privileges and re-launch if necessary
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "This script requires administrative privileges. Attempting to re-launch as an administrator..."
    Start-Process powershell -Verb runAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$serviceName = "postgresql-x64-18"

Write-Host "Restarting PostgreSQL service: $serviceName"

$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (!$service) {
    Write-Host "Service $serviceName not found."
    exit 1
}

if ($service.Status -eq "Running") {
    Write-Host "Stopping service..."
    Stop-Service -Name $serviceName -Force
    Start-Sleep -Seconds 3
}

Write-Host "Starting service..."
Start-Service -Name $serviceName

Write-Host "Service restarted successfully."
Get-Service -Name $serviceName