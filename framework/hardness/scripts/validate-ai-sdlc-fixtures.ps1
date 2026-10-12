[CmdletBinding()]
param(
    [string]$SchemaPath,
    [string]$ValidFixturePath,
    [string]$InvalidFixturePath
)

$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($SchemaPath)) { $SchemaPath = Join-Path $scriptDirectory '..\ai-sdlc-schema.json' }
if ([string]::IsNullOrWhiteSpace($ValidFixturePath)) { $ValidFixturePath = Join-Path $scriptDirectory '..\fixtures\valid-ai-sdlc.json' }
if ([string]::IsNullOrWhiteSpace($InvalidFixturePath)) { $InvalidFixturePath = Join-Path $scriptDirectory '..\fixtures\invalid-ai-sdlc-missing-level.json' }

function Get-JsonObject {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required AI-SDLC validation input is missing: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Test-RequiredFields {
    param($Object, [string[]]$Fields, [string]$Context, [System.Collections.Generic.List[string]]$Errors)

    if ($null -eq $Object) {
        $Errors.Add("$Context is null.")
        return
    }
    foreach ($field in $Fields) {
        if ($Object.PSObject.Properties.Name -notcontains $field) {
            $Errors.Add("$Context is missing required field '$field'.")
        }
    }
}

function Test-StringArray {
    param($Value, [string]$Context, [System.Collections.Generic.List[string]]$Errors)

    if ($null -eq $Value -or @($Value).Count -eq 0 -or @($Value | Where-Object { $_ -isnot [string] -or $_.Length -eq 0 }).Count -gt 0) {
        $Errors.Add("$Context must be a non-empty array of non-empty strings.")
    }
}

function Test-EnumValue {
    param($Value, [string[]]$Allowed, [string]$Context, [System.Collections.Generic.List[string]]$Errors)

    if ($Allowed -notcontains $Value) {
        $Errors.Add("$Context must be one of: $($Allowed -join ', ').")
    }
}

function Test-RateValue {
    param($Value, [string]$Context, [System.Collections.Generic.List[string]]$Errors)

    if ($Value -isnot [double] -and $Value -isnot [int] -or $Value -lt 0.0 -or $Value -gt 1.0) {
        $Errors.Add("$Context must be a floating point rate between 0.0 and 1.0.")
    }
}

function Test-AiSdlcRecord {
    param($Config, $Schema)

    $errors = [System.Collections.Generic.List[string]]::new()
    Test-RequiredFields $Config $Schema.required 'ai-sdlc config' $errors

    if ($Config.version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
        $errors.Add('config.version must be a valid SemVer string.')
    }

    $autonomyLevels = @('shadow', 'suggest', 'auto-PR', 'auto-merge-low', 'auto-merge-all', 'auto-deploy')

    # trust_ladder
    Test-RequiredFields $Config.trust_ladder $Schema.properties.trust_ladder.required 'config.trust_ladder' $errors
    if ($null -ne $Config.trust_ladder) {
        Test-EnumValue $Config.trust_ladder.current_level $autonomyLevels 'config.trust_ladder.current_level' $errors
        Test-EnumValue $Config.trust_ladder.target_level $autonomyLevels 'config.trust_ladder.target_level' $errors

        Test-RequiredFields $Config.trust_ladder.evaluation_window $Schema.properties.trust_ladder.properties.evaluation_window.required 'config.trust_ladder.evaluation_window' $errors
        if ($null -ne $Config.trust_ladder.evaluation_window) {
            if ($Config.trust_ladder.evaluation_window.min_pull_requests -lt 1) { $errors.Add('min_pull_requests must be >= 1.') }
            if ($Config.trust_ladder.evaluation_window.min_days -lt 1) { $errors.Add('min_days must be >= 1.') }
        }

        Test-RequiredFields $Config.trust_ladder.promotion_gates $Schema.properties.trust_ladder.properties.promotion_gates.required 'config.trust_ladder.promotion_gates' $errors
        if ($null -ne $Config.trust_ladder.promotion_gates) {
            Test-RateValue $Config.trust_ladder.promotion_gates.min_merge_success_rate 'min_merge_success_rate' $errors
            Test-RateValue $Config.trust_ladder.promotion_gates.max_revert_rate 'max_revert_rate' $errors
            Test-RateValue $Config.trust_ladder.promotion_gates.max_escalation_rate 'max_escalation_rate' $errors
            Test-RateValue $Config.trust_ladder.promotion_gates.min_ci_first_pass_rate 'min_ci_first_pass_rate' $errors
            Test-RateValue $Config.trust_ladder.promotion_gates.min_policy_conformance_rate 'min_policy_conformance_rate' $errors
        }

        Test-RequiredFields $Config.trust_ladder.demotion_triggers $Schema.properties.trust_ladder.properties.demotion_triggers.required 'config.trust_ladder.demotion_triggers' $errors
        if ($null -ne $Config.trust_ladder.demotion_triggers) {
            Test-EnumValue $Config.trust_ladder.demotion_triggers.demote_to_level $autonomyLevels 'config.trust_ladder.demotion_triggers.demote_to_level' $errors
        }

        Test-RequiredFields $Config.trust_ladder.rehabilitation $Schema.properties.trust_ladder.properties.rehabilitation.required 'config.trust_ladder.rehabilitation' $errors
        if ($null -ne $Config.trust_ladder.rehabilitation) {
            if ($Config.trust_ladder.rehabilitation.cooldown_days -lt 0) { $errors.Add('cooldown_days must be >= 0.') }
            if ($Config.trust_ladder.rehabilitation.required_clean_runs -lt 1) { $errors.Add('required_clean_runs must be >= 1.') }
        }
    }

    # risk_boundaries
    Test-RequiredFields $Config.risk_boundaries $Schema.properties.risk_boundaries.required 'config.risk_boundaries' $errors
    if ($null -ne $Config.risk_boundaries) {
        Test-StringArray $Config.risk_boundaries.low_risk_paths 'config.risk_boundaries.low_risk_paths' $errors
        Test-StringArray $Config.risk_boundaries.high_risk_paths 'config.risk_boundaries.high_risk_paths' $errors
        Test-StringArray $Config.risk_boundaries.protected_branches 'config.risk_boundaries.protected_branches' $errors
    }

    # automated_merge_rules
    Test-RequiredFields $Config.automated_merge_rules $Schema.properties.automated_merge_rules.required 'config.automated_merge_rules' $errors
    if ($null -ne $Config.automated_merge_rules) {
        Test-StringArray $Config.automated_merge_rules.allowed_merge_methods 'config.automated_merge_rules.allowed_merge_methods' $errors
    }

    # audit_and_observability
    Test-RequiredFields $Config.audit_and_observability $Schema.properties.audit_and_observability.required 'config.audit_and_observability' $errors
    if ($null -ne $Config.audit_and_observability) {
        Test-EnumValue $Config.audit_and_observability.evidence_retention @('repository-record', 'external-record', 'ephemeral') 'evidence_retention' $errors
        Test-EnumValue $Config.audit_and_observability.metrics_collection @('git-native', 'ci-telemetry', 'external-apm') 'metrics_collection' $errors
    }

    return ,$errors
}

$schema = Get-JsonObject $SchemaPath
$validErrors = Test-AiSdlcRecord (Get-JsonObject $ValidFixturePath) $schema
$invalidErrors = Test-AiSdlcRecord (Get-JsonObject $InvalidFixturePath) $schema

if ($validErrors.Count -gt 0) {
    throw "Expected valid fixture to satisfy schema: $($validErrors -join ' ')"
}

if ($invalidErrors.Count -eq 0) {
    throw 'Expected invalid fixture to fail schema.'
}

Write-Output 'Hardness AI-SDLC fixtures validated: valid accepted; invalid rejected.'
Write-Output "Invalid fixture rejection: $($invalidErrors -join ' ')"
