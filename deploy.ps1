# PowerShell Script for RSD Analysis Agent Deployment

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "schedule", "test", "unschedule", "logs")]
    [string]$Action = "setup",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("hourly", "daily", "on-login")]
    [string]$ScheduleType = "hourly"
)

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Setup-Agent {
    Write-Header "RSD Analysis Agent - Setup"
    
    # Check admin rights
    if (-not (Test-Admin)) {
        Write-Host "ERROR: This script must run as Administrator" -ForegroundColor Red
        exit 1
    }
    
    # Check Python
    Write-Host "Checking Python installation..." -ForegroundColor Yellow
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    
    if (-not $pythonPath) {
        Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Found Python: $pythonPath" -ForegroundColor Green
    
    # Create venv
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    if (-not (Test-Path "venv")) {
        & python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Virtual environment already exists" -ForegroundColor Green
    }
    
    # Activate venv and install
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & .\venv\Scripts\pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    
    # Setup .env
    if (-not (Test-Path ".env")) {
        Write-Host "Creating .env from template..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "Opening .env for editing..." -ForegroundColor Yellow
        notepad.exe .env
    }
    
    # Run setup check
    Write-Host "Running setup checks..." -ForegroundColor Yellow
    & .\venv\Scripts\python setup_check.py
    
    Write-Header "Setup Complete!"
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  1. Download credentials.json from Google Cloud Console"
    Write-Host "  2. Place in project root directory"
    Write-Host "  3. Run: PS> .\deploy.ps1 -Action test"
    Write-Host "  4. Then: PS> .\deploy.ps1 -Action schedule"
}

function Schedule-Agent {
    Write-Header "Scheduling RSD Analysis Agent"
    
    if (-not (Test-Admin)) {
        Write-Host "ERROR: Must run as Administrator to schedule tasks" -ForegroundColor Red
        exit 1
    }
    
    $projectDir = Get-Location
    $pythonExe = Join-Path $projectDir "venv\Scripts\python.exe"
    $mainScript = Join-Path $projectDir "main.py"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Host "ERROR: Python executable not found. Run setup first." -ForegroundColor Red
        exit 1
    }
    
    $taskName = "RSD-Analysis-Agent"
    
    # Remove existing task if present
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing scheduled task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    # Create task action
    $action = New-ScheduledTaskAction `
        -Execute $pythonExe `
        -Argument $mainScript `
        -WorkingDirectory $projectDir
    
    # Create trigger based on type
    switch ($ScheduleType) {
        "hourly" {
            $trigger = New-ScheduledTaskTrigger `
                -Once `
                -At (Get-Date) `
                -RepetitionInterval (New-TimeSpan -Hours 1) `
                -RepetitionDuration (New-TimeSpan -Hours 24)
            Write-Host "Schedule: Every hour (24 hours per day)" -ForegroundColor Green
        }
        "daily" {
            $trigger = New-ScheduledTaskTrigger `
                -Daily `
                -At "08:00"
            Write-Host "Schedule: Daily at 8:00 AM" -ForegroundColor Green
        }
        "on-login" {
            $trigger = New-ScheduledTaskTrigger -AtLogOn
            Write-Host "Schedule: At user login" -ForegroundColor Green
        }
    }
    
    # Create task settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable
    
    # Register task
    Write-Host "Creating scheduled task '$taskName'..." -ForegroundColor Yellow
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -Force
    
    Write-Host "Task scheduled successfully!" -ForegroundColor Green
    Write-Host "View in Task Scheduler: taskmgr.exe" -ForegroundColor Green
}

function Test-Agent {
    Write-Header "Testing RSD Analysis Agent"
    
    Write-Host "Running agent in test mode..." -ForegroundColor Yellow
    & .\venv\Scripts\python main.py
}

function Unschedule-Agent {
    Write-Header "Unscheduling RSD Analysis Agent"
    
    if (-not (Test-Admin)) {
        Write-Host "ERROR: Must run as Administrator" -ForegroundColor Red
        exit 1
    }
    
    $taskName = "RSD-Analysis-Agent"
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if (-not $task) {
        Write-Host "Task '$taskName' not found" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Unregistering task '$taskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$true
    Write-Host "Task removed" -ForegroundColor Green
}

function Show-Logs {
    Write-Header "RSD Analysis Agent - Recent Logs"
    
    $taskName = "RSD-Analysis-Agent"
    
    Write-Host "Last 10 task executions:" -ForegroundColor Green
    Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" `
        -FilterXPath "*[System[EventID=102] and EventData[Data[@Name='TaskName']='\\$taskName']]" `
        -MaxEvents 10 -ErrorAction SilentlyContinue | 
        ForEach-Object {
            Write-Host "$($_.TimeCreated): $($_.Message)" -ForegroundColor Gray
        }
}

# Main execution
switch ($Action) {
    "setup" { Setup-Agent }
    "schedule" { Schedule-Agent }
    "test" { Test-Agent }
    "unschedule" { Unschedule-Agent }
    "logs" { Show-Logs }
    default { Write-Host "Unknown action: $Action"; exit 1 }
}
