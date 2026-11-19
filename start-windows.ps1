param(
    [string]$HostIp
)

$ErrorActionPreference = 'Stop'

function Test-UsableIPv4 {
    param([string]$Address)

    if ($Address -notmatch '^(?:0|[1-9]\d{0,2})(?:\.(?:0|[1-9]\d{0,2})){3}$') {
        return $false
    }

    $parsed = $null
    if (-not [System.Net.IPAddress]::TryParse($Address, [ref]$parsed) -or
        $parsed.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
        return $false
    }

    $octets = $parsed.GetAddressBytes()
    return $octets[0] -ne 0 -and $octets[0] -ne 127 -and
        -not ($octets[0] -eq 169 -and $octets[1] -eq 254) -and
        $octets[0] -lt 224
}

function Test-PrivateIPv4 {
    param([string]$Address)

    $octets = ([System.Net.IPAddress]::Parse($Address)).GetAddressBytes()
    return $octets[0] -eq 10 -or
        ($octets[0] -eq 172 -and $octets[1] -ge 16 -and $octets[1] -le 31) -or
        ($octets[0] -eq 192 -and $octets[1] -eq 168)
}

function Get-LanIPv4 {
    $physicalAdapters = @{}
    try {
        foreach ($adapter in @(Get-NetAdapter -Physical -ErrorAction Stop)) {
            if ($adapter.Status -eq 'Up') {
                $physicalAdapters[[int]$adapter.ifIndex] = $true
            }
        }
    } catch {
        # Address selection still works if this adapter hint is unavailable.
    }

    try {
        $configurations = @(Get-NetIPConfiguration -ErrorAction Stop)
    } catch {
        throw 'Could not inspect network adapters. Pass the computer LAN address with -HostIp YOUR_IP.'
    }

    $best = $null
    $bestScore = -1
    foreach ($config in $configurations) {
        if ($config.NetAdapter -and $config.NetAdapter.Status -ne 'Up') {
            continue
        }

        $adapterName = [string]$config.InterfaceAlias
        if ($adapterName -match '(?i)vEthernet|Docker|Tailscale|ZeroTier|WireGuard|\bVPN\b|\bTAP\b|Loopback|VirtualBox|VMware|Hyper-V') {
            continue
        }

        foreach ($entry in @($config.IPv4Address)) {
            if ($null -eq $entry) {
                continue
            }

            $address = [string]$entry.IPAddress
            if (-not (Test-UsableIPv4 $address)) {
                continue
            }

            $score = 0
            if (Test-PrivateIPv4 $address) { $score += 100 }
            if ($physicalAdapters.ContainsKey([int]$config.InterfaceIndex)) { $score += 40 }
            if ($adapterName -match '(?i)Wi-Fi|WLAN|Wireless') { $score += 20 }
            if ($config.IPv4DefaultGateway) { $score += 10 }

            if ($score -gt $bestScore) {
                $best = [pscustomobject]@{ Address = $address; Adapter = $adapterName }
                $bestScore = $score
            }
        }
    }

    if ($null -eq $best) {
        throw 'No usable LAN IPv4 address was found. Connect to Wi-Fi or Ethernet, or run .\start-windows.ps1 -HostIp YOUR_IP.'
    }
    return $best
}

function Get-PortListeners {
    if (-not (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue)) {
        return
    }

    try {
        Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue |
            Where-Object { $_.LocalAddress -notmatch ':' }
    } catch {
        # Docker will still report a bind failure if this optional check is unavailable.
    }
}

function Assert-PortAvailable {
    $listeners = @(Get-PortListeners)
    if ($listeners.Count -eq 0) {
        return
    }

    # A second run may find the port held by this project's own running container.
    $runningContainers = @(& docker compose ps --quiet your-reflection 2>$null)
    if ($LASTEXITCODE -eq 0 -and $runningContainers.Count -gt 0) {
        $publishedPorts = @(& docker compose port your-reflection 8765 2>$null)
        if ($LASTEXITCODE -eq 0 -and @($publishedPorts | Where-Object { $_ -match ':8765\s*$' }).Count -gt 0) {
            return
        }
    }

    $processIds = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 0 })
    $owner = if ($processIds.Count -gt 0) { ' (PID ' + ($processIds -join ', ') + ')' } else { '' }
    throw "TCP port 8765 is already in use${owner}. Stop that process and run this script again."
}

try {
    if ($HostIp -and -not (Test-UsableIPv4 $HostIp)) {
        throw '-HostIp must be a usable IPv4 address, for example 192.168.1.23.'
    }

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker was not found. Install Docker Desktop and start it before running this script.'
    }

    # Windows PowerShell may surface native stderr as an error even when Docker succeeds.
    $previousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & docker compose version *> $null
        if ($LASTEXITCODE -ne 0) {
            throw 'Docker Compose is unavailable. Install or update Docker Desktop with Compose support.'
        }

        & docker info --format '{{.ServerVersion}}' *> $null
        if ($LASTEXITCODE -ne 0) {
            throw 'The Docker engine is not running or is inaccessible. Start Docker Desktop and try again.'
        }

        $missing = @()
        foreach ($file in @('compose.yaml', 'Dockerfile', 'launch_demo.py')) {
            if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $file) -PathType Leaf)) {
                $missing += $file
            }
        }
        foreach ($directory in @('dist', 'vendor')) {
            if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $directory) -PathType Container)) {
                $missing += $directory
            }
        }
        if ($missing.Count -gt 0) {
            throw ('Incomplete project folder: missing {0}. Extract or clone the full project and try again.' -f ($missing -join ', '))
        }

        if ($HostIp) {
            $selected = [pscustomobject]@{ Address = $HostIp; Adapter = 'manual selection' }
        } else {
            $selected = Get-LanIPv4
        }

        $env:PUBLIC_HOST = $selected.Address
        Write-Host "Using LAN address $($selected.Address) ($($selected.Adapter))."

        Push-Location -LiteralPath $PSScriptRoot -ErrorAction Stop
        try {
            Assert-PortAvailable
            Write-Host 'Building and starting Your Reflection...'
            & docker compose up --build --detach
            if ($LASTEXITCODE -ne 0) {
                Assert-PortAvailable
                throw 'Docker Compose could not start the demo. Check the Docker error above; port 8765 may be in use. Run docker compose logs from the project folder for details.'
            }

            $ready = $false
            $containerExited = $false
            for ($attempt = 0; $attempt -lt 30; $attempt++) {
                try {
                    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/gift-card.html' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
                    if ($response.StatusCode -eq 200) {
                        $ready = $true
                        break
                    }
                } catch {
                    # The service may need a moment to finish starting.
                }

                $runningContainers = @(& docker compose ps --quiet your-reflection 2>$null)
                if ($LASTEXITCODE -eq 0 -and $runningContainers.Count -eq 0) {
                    $containerExited = $true
                    break
                }
                Start-Sleep -Seconds 1
            }

            if (-not $ready) {
                Write-Host 'Recent container logs:'
                & docker compose logs --tail 40 your-reflection
                if ($containerExited) {
                    throw 'The demo container exited during startup. Check its logs above.'
                }
                throw 'The demo started, but the gift card did not respond at http://127.0.0.1:8765/gift-card.html. Check the logs above and whether port 8765 is reachable.'
            }
        } finally {
            Pop-Location
        }
    } finally {
        $ErrorActionPreference = $previousErrorPreference
    }

    $siteUrl = 'http://{0}:8765/' -f $selected.Address
    Write-Host ''
    Write-Host "Site:      $siteUrl"
    Write-Host "Gift card: ${siteUrl}gift-card.html"
    Write-Host 'Demo code: 271846'
    Write-Host 'Open the gift card URL in a browser. Phones must be on the same Wi-Fi or LAN.'
    Write-Host 'To stop, run docker compose down from the project folder.'
} catch {
    Write-Error -Message $_.Exception.Message -ErrorAction Continue
    exit 1
}
