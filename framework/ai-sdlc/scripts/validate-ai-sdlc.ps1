[CmdletBinding()]
param(
    [string]$ConfigFile = ".ai-sdlc.yaml",
    [string]$SchemaFile = ""
)

$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDirectory "validate-ai-sdlc.py"

$pythonArgs = @($pythonScript, $ConfigFile)
if (-not [string]::IsNullOrWhiteSpace($SchemaFile)) {
    $pythonArgs += @("--schema", $SchemaFile)
}

python3 @pythonArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
