# Simple script to load environment variables from secrets.env

$envFile = "C:\Users\nites\realtimestockstracking\secrets.env"

Write-Host "Loading environment variables from: $envFile" -ForegroundColor Green

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    
    # Skip empty lines and comments
    if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
        return
    }
    
    # Parse KEY=VALUE
    if ($line -match '^\s*([^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        
        # Set environment variable
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
        Write-Host "Set: $name" -ForegroundColor Cyan
    }
}

Write-Host "Variables loaded successfully!" -ForegroundColor Green

# Verify Snowflake variables
Write-Host "`nVerifying:" -ForegroundColor Green
Write-Host "SNOWFLAKE_ACCOUNT: $([Environment]::GetEnvironmentVariable('SNOWFLAKE_ACCOUNT', 'Process'))" -ForegroundColor Cyan
Write-Host "SNOWFLAKE_USER: $([Environment]::GetEnvironmentVariable('SNOWFLAKE_USER', 'Process'))" -ForegroundColor Cyan
Write-Host "SNOWFLAKE_DATABASE: $([Environment]::GetEnvironmentVariable('SNOWFLAKE_DATABASE', 'Process'))" -ForegroundColor Cyan
