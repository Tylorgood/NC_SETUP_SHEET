param(
  [string]$InstallRoot = "$env:USERPROFILE\plugins",
  [string]$MarketplacePath = "$env:USERPROFILE\.agents\plugins\marketplace.json"
)

$ErrorActionPreference = "Stop"

$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginName = "mcam-assistant"
$TargetRoot = Join-Path $InstallRoot $PluginName

Write-Host "Installing $PluginName from:"
Write-Host "  $SourceRoot"
Write-Host "To:"
Write-Host "  $TargetRoot"

New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
if (Test-Path -LiteralPath $TargetRoot) {
  Remove-Item -LiteralPath $TargetRoot -Recurse -Force
}
Copy-Item -LiteralPath $SourceRoot -Destination $TargetRoot -Recurse -Force

$MarketplaceDir = Split-Path -Parent $MarketplacePath
New-Item -ItemType Directory -Force -Path $MarketplaceDir | Out-Null

if (Test-Path -LiteralPath $MarketplacePath) {
  $marketplace = Get-Content -Raw -LiteralPath $MarketplacePath | ConvertFrom-Json
  if (-not $marketplace.plugins) {
    $marketplace | Add-Member -MemberType NoteProperty -Name plugins -Value @()
  }
} else {
  $marketplace = [pscustomobject]@{
    name = "personal"
    interface = [pscustomobject]@{
      displayName = "Personal"
    }
    plugins = @()
  }
}

$existing = @($marketplace.plugins | Where-Object { $_.name -eq $PluginName })
if ($existing.Count -eq 0) {
  $entry = [pscustomobject]@{
    name = $PluginName
    source = [pscustomobject]@{
      source = "local"
      path = "./plugins/$PluginName"
    }
    policy = [pscustomobject]@{
      installation = "AVAILABLE"
      authentication = "ON_INSTALL"
    }
    category = "Productivity"
  }
  $marketplace.plugins = @($marketplace.plugins) + $entry
}

$marketplace | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $MarketplacePath -Encoding UTF8

Write-Host ""
Write-Host "Installed."
Write-Host "CLI test:"
Write-Host "  python `"$TargetRoot\scripts\mcam_assistant_cli.py`" --nc `"C:\path\program.nc`" --out `"C:\path\setup_package`""
Write-Host ""
Write-Host "Codex plugin install:"
Write-Host "  codex plugin add mcam-assistant@personal"
