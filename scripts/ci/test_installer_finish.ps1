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
    $setupProcessPrefix = [IO.Path]::GetFileNameWithoutExtension($Installer)
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
    $pageOpened = $false
    $lastWindowName = ''
    $lastButtonNames = ''
    $lastUiSignature = ''

    while (-not $setup.HasExited -and [DateTime]::UtcNow -lt $deadline) {
        $setup.Refresh()
        if (Test-Path -LiteralPath $logPath) {
            $currentLog = Get-Content -LiteralPath $logPath -Raw
            if ($currentLog.Contains("Opened thank-you page: $ExpectedUrl")) {
                $pageOpened = $true
                break
            }
            if ($currentLog -match 'Unable to open the thank-you page:') {
                throw "Installer could not open $ExpectedUrl. See $logPath"
            }
        }
        if ($finishClicked) {
            Start-Sleep -Milliseconds 250
            continue
        }
        $setupProcesses = @(
            Get-Process -ErrorAction SilentlyContinue |
                Where-Object { $_.ProcessName -like "$setupProcessPrefix*" }
        )
        foreach ($setupProcess in $setupProcesses) {
            $setupProcess.Refresh()
            if ($setupProcess.MainWindowHandle -eq 0) {
                continue
            }
            $buttonInvoked = $false
            try {
                $window = [System.Windows.Automation.AutomationElement]::FromHandle(
                    $setupProcess.MainWindowHandle
                )
                $condition = [System.Windows.Automation.PropertyCondition]::new(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                    [System.Windows.Automation.ControlType]::Button
                )
                $buttons = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
                $lastWindowName = $window.Current.Name
                $lastButtonNames = (@($buttons | ForEach-Object { $_.Current.Name }) -join ' | ')
                $uiSignature = "$($setupProcess.Id)|$lastWindowName|$lastButtonNames"
                if ($uiSignature -ne $lastUiSignature) {
                    Write-Host "Installer UI [$($setupProcess.Id)] '$lastWindowName': $lastButtonNames"
                    $lastUiSignature = $uiSignature
                }
                foreach ($button in $buttons) {
                    $name = $button.Current.Name.Trim()
                    if ($name -match '^\s*&?\s*(Next|Siguiente)\s*>?\s*$' -or
                        $name -match '^\s*&?\s*(Install|Instalar)\s*$') {
                        $button.GetCurrentPattern(
                            [System.Windows.Automation.InvokePattern]::Pattern
                        ).Invoke()
                        $buttonInvoked = $true
                        Start-Sleep -Milliseconds 350
                        break
                    }
                    if ($name -match '^\s*&?\s*(Finish|Finalizar)\s*$') {
                        $button.GetCurrentPattern(
                            [System.Windows.Automation.InvokePattern]::Pattern
                        ).Invoke()
                        $finishClicked = $true
                        $buttonInvoked = $true
                        Start-Sleep -Milliseconds 350
                        break
                    }
                }
            } catch {
                # The wizard can replace its page while UI Automation is reading it.
            }
            if ($buttonInvoked) {
                break
            }
        }
        Start-Sleep -Milliseconds 250
    }

    if ($pageOpened) {
        if (-not $finishClicked) {
            throw "The thank-you page opened before the Finish button was confirmed for $Language"
        }
        Write-Host "Installer opened $ExpectedUrl"
        Get-Process -Name 'Yagua' -ErrorAction SilentlyContinue | Stop-Process -Force
        Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.ProcessName -like "$setupProcessPrefix*" } |
            Stop-Process -Force -ErrorAction SilentlyContinue
        return
    }

    if (-not $setup.HasExited) {
        Stop-Process -Id $setup.Id -Force
        throw "Installer timed out for language $Language. Last window: '$lastWindowName'. Buttons: $lastButtonNames"
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
