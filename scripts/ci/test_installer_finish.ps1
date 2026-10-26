param(
    [Parameter(Mandatory = $true)][string]$Installer,
    [Parameter(Mandatory = $true)][string]$WorkDirectory
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

function Test-InstallerFinish([string]$Language, [string]$ExpectedUrl) {
    $installDirectory = Join-Path $WorkDirectory "installed-$Language"
    $group = "Yagua candidate test $Language"
    $logPath = Join-Path $WorkDirectory "setup-$Language.log"
    $arguments = @(
        "/LANG=$Language",
        "/DIR=`"$installDirectory`"",
        "/GROUP=`"$group`"",
        '/NOICONS',
        "/LOG=`"$logPath`""
    )
    $setup = Start-Process -FilePath $Installer -ArgumentList $arguments -PassThru
    $deadline = [DateTime]::UtcNow.AddMinutes(15)
    $finishClicked = $false

    while (-not $setup.HasExited -and [DateTime]::UtcNow -lt $deadline) {
        $setup.Refresh()
        if ($setup.MainWindowHandle -ne 0) {
            try {
                $window = [System.Windows.Automation.AutomationElement]::FromHandle($setup.MainWindowHandle)
                $condition = [System.Windows.Automation.PropertyCondition]::new(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Button
                )
                $buttons = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
                foreach ($button in $buttons) {
                    $name = $button.Current.Name.Trim()
                    if ($name -match '^(Next\s*>|Siguiente\s*>)$' -or
                        $name -match '^(Install|Instalar)$') {
                        $button.GetCurrentPattern(
                            [System.Windows.Automation.InvokePattern]::Pattern
                        ).Invoke()
                        Start-Sleep -Milliseconds 350
                        break
                    }
                    if ($name -match '^(Finish|Finalizar)$') {
                        $button.GetCurrentPattern(
                            [System.Windows.Automation.InvokePattern]::Pattern
                        ).Invoke()
                        $finishClicked = $true
                        Start-Sleep -Milliseconds 350
                        break
                    }
                }
            } catch {
                # The wizard can replace its page while UI Automation is reading it.
            }
        }
        Start-Sleep -Milliseconds 250
    }

    if (-not $setup.HasExited) {
        Stop-Process -Id $setup.Id -Force
        throw "Installer timed out for language $Language"
    }
    if ($setup.ExitCode -ne 0) {
        throw "Installer exited with code $($setup.ExitCode) for language $Language"
    }
    if (-not $finishClicked) {
        throw "The Finish button was not reached for language $Language"
    }

    $logDeadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        if (Test-Path -LiteralPath $logPath) {
            $log = Get-Content -LiteralPath $logPath -Raw
            if ($log.Contains("Opened thank-you page: $ExpectedUrl")) {
                Write-Host "Installer opened $ExpectedUrl"
                Get-Process -Name 'Yagua' -ErrorAction SilentlyContinue | Stop-Process -Force
                return
            }
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $logDeadline)

    if ($log -match 'Unable to open the thank-you page:') {
        throw "Installer could not open $ExpectedUrl. See $logPath"
    }
    throw "Installer did not log opening $ExpectedUrl. See $logPath"
}

New-Item -ItemType Directory -Path $WorkDirectory -Force | Out-Null
Test-InstallerFinish 'spanish' 'https://yagua.bouixdev.workers.dev/es/thanks/'
Test-InstallerFinish 'english' 'https://yagua.bouixdev.workers.dev/en/thanks/'
