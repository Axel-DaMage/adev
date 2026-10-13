[CmdletBinding()]
param(
    [string]$SchemaPath,
    [string]$ValidFixturePath,
    [string]$InvalidFixturePath
)

$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($SchemaPath)) {
    $SchemaPath = Join-Path $scriptDirectory '..\issue-dor-schema.json'
}
if ([string]::IsNullOrWhiteSpace($ValidFixturePath)) {
    $ValidFixturePath = Join-Path $scriptDirectory '..\fixtures\valid-agent-issue.json'
}
if ([string]::IsNullOrWhiteSpace($InvalidFixturePath)) {
    $InvalidFixturePath = Join-Path $scriptDirectory '..\fixtures\invalid-agent-issue-missing-ac.json'
}

function Test-JsonFile {
    param([string]$Path)
    if (-not (Test-Path -Path $Path -PathType Leaf)) {
        throw "File not found: $Path"
    }
    try {
        return (Get-Content -Raw -Path $Path | ConvertFrom-Json)
    }
    catch {
        throw "Failed to parse JSON file '$Path': $_"
    }
}

$schema = Test-JsonFile -Path $SchemaPath
$validFixture = Test-JsonFile -Path $ValidFixturePath
$invalidFixture = Test-JsonFile -Path $InvalidFixturePath

$requiredProperties = @(
    'id',
    'title',
    'type',
    'priority',
    'risk_tier',
    'context',
    'objective',
    'in_scope',
    'out_of_scope',
    'acceptance_criteria',
    'context_attachments',
    'verification_contract'
)

foreach ($property in $requiredProperties) {
    if (-not ($validFixture.PSObject.Properties.Name -contains $property)) {
        throw "Valid fixture missing required property '$property'."
    }
}

if ($validFixture.acceptance_criteria.Count -eq 0) {
    throw "Valid fixture must contain at least one acceptance criterion."
}

if ($invalidFixture.PSObject.Properties.Name -contains 'acceptance_criteria' -and $invalidFixture.acceptance_criteria.Count -gt 0) {
    throw "Invalid fixture was expected to fail acceptance criteria validation."
}

Write-Host "Issue Definition-of-Ready schema and fixtures validated successfully."
