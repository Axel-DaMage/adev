[CmdletBinding()]
param(
    [string]$SchemaPath,
    [string]$BaselineFixturePath,
    [string]$ValidOverrideFixturePath,
    [string]$ViolationOverrideFixturePath,
    [string]$ExpectedResolvedFixturePath
)

$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($SchemaPath)) { $SchemaPath = Join-Path $scriptDirectory '..\ai-sdlc-schema.json' }
if ([string]::IsNullOrWhiteSpace($BaselineFixturePath)) { $BaselineFixturePath = Join-Path $scriptDirectory '..\fixtures\ai-sdlc\org-baseline.json' }
if ([string]::IsNullOrWhiteSpace($ValidOverrideFixturePath)) { $ValidOverrideFixturePath = Join-Path $scriptDirectory '..\fixtures\ai-sdlc\repo-override-valid.json' }
if ([string]::IsNullOrWhiteSpace($ViolationOverrideFixturePath)) { $ViolationOverrideFixturePath = Join-Path $scriptDirectory '..\fixtures\ai-sdlc\repo-override-floor-violation.json' }
if ([string]::IsNullOrWhiteSpace($ExpectedResolvedFixturePath)) { $ExpectedResolvedFixturePath = Join-Path $scriptDirectory '..\fixtures\ai-sdlc\resolved-policy-expected.json' }

function Get-JsonObject {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required AI SDLC validation input is missing: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Test-RequiredFields {
    param($Object, [string[]]$Fields, [string]$Context, [System.Collections.Generic.List[string]]$Errors)

    foreach ($field in $Fields) {
        if ($null -eq $Object -or $Object.PSObject.Properties.Name -notcontains $field) {
            $Errors.Add("$Context is missing required field '$field'.")
        }
    }
}

function Test-AiSdlcDoc {
    param($Doc, $Schema, [string]$Context)

    $errors = [System.Collections.Generic.List[string]]::new()
    Test-RequiredFields $Doc $Schema.required $Context $errors

    if ($Doc.schema_version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
        $errors.Add("$Context.schema_version must follow semantic versioning.")
    }

    Test-RequiredFields $Doc.metadata $Schema.properties.metadata.required "$Context.metadata" $errors
    if ($Doc.metadata.scope -notin @('organization', 'repository', 'group')) {
        $errors.Add("$Context.metadata.scope must be 'organization', 'repository', or 'group'.")
    }

    return ,$errors
}

$schema = Get-JsonObject $SchemaPath
$baseline = Get-JsonObject $BaselineFixturePath
$validOverride = Get-JsonObject $ValidOverrideFixturePath
$violationOverride = Get-JsonObject $ViolationOverrideFixturePath
$resolvedExpected = Get-JsonObject $ExpectedResolvedFixturePath

$baselineErrors = Test-AiSdlcDoc $baseline $schema 'org-baseline'
if ($baselineErrors.Count -gt 0) {
    throw "Org baseline fixture failed schema validation:`n$($baselineErrors -join "`n")"
}

$validOverrideErrors = Test-AiSdlcDoc $validOverride $schema 'repo-override-valid'
if ($validOverrideErrors.Count -gt 0) {
    throw "Valid repo override fixture failed schema validation:`n$($validOverrideErrors -join "`n")"
}

$resolvedExpectedErrors = Test-AiSdlcDoc $resolvedExpected $schema 'resolved-policy-expected'
if ($resolvedExpectedErrors.Count -gt 0) {
    throw "Expected resolved policy fixture failed schema validation:`n$($resolvedExpectedErrors -join "`n")"
}

Write-Output "AI SDLC fixtures validated against schema successfully."
