Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue |
    Select-Object -Unique OwningProcess |
    ForEach-Object {
        Write-Host "Killing PID $($_.OwningProcess)"
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
Start-Sleep 3
$count = (Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue | Measure-Object).Count
if ($count -eq 0) {
    Write-Host "Port 8001 is now free"
} else {
    Write-Host "Port 8001 still in use"
    Get-NetTCPConnection -LocalPort 8001 | Format-Table
}
