# Inspect only disposable synthetic QA evidence; never change a real profile.
param([Parameter(Mandatory = $true)][string]$Output)
$ErrorActionPreference = 'Stop'

function Get-AclObservation {
    param([string]$Path, [string]$Label)
    $acl = Get-Acl -LiteralPath $Path
    $raw = [System.Security.AccessControl.RawSecurityDescriptor]::new(
        $acl.GetSecurityDescriptorBinaryForm(), 0)
    if ($null -eq $raw.DiscretionaryAcl) { throw 'Null DACL' }
    $rules = @($acl.GetAccessRules($true, $true,
        [System.Security.Principal.SecurityIdentifier]))
    $broad = @('S-1-1-0', 'S-1-5-11', 'S-1-5-32-545', 'S-1-5-32-546')
    $allow = @($rules | Where-Object {
        $_.AccessControlType -eq 'Allow' -and $_.IdentityReference.Value -in $broad
    })
    $read = @($allow | Where-Object { ([int64]$_.FileSystemRights -band 1) -ne 0 })
    $write = @($allow | Where-Object {
        ([int64]$_.FileSystemRights -band (2 -bor 4 -bor 16 -bor 64 -bor 256 -bor 65536 -bor 262144 -bor 524288)) -ne 0
    })
    $owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $current = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $ownerClass = if ($owner.Value -eq $current.Value) { 'RUNNER' }
        elseif ($owner.Value -eq 'S-1-5-32-544') { 'ADMINISTRATORS' }
        elseif ($owner.Value -eq 'S-1-5-18') { 'SYSTEM' }
        else { 'OTHER' }
    [ordered]@{
        label = $Label
        owner_class = $ownerClass
        owner_is_runner = ($owner.Value -eq $current.Value)
        protected = $acl.AreAccessRulesProtected
        canonical = $acl.AreAccessRulesCanonical
        rule_count = $rules.Count
        inherited_count = @($rules | Where-Object IsInherited).Count
        broad_allow_count = $allow.Count
        broad_read_count = $read.Count
        broad_write_count = $write.Count
        broad_explicit_read_count = @($read | Where-Object { -not $_.IsInherited }).Count
    }
}

$scratch = Join-Path ([System.IO.Path]::GetTempPath()) ('ajazz-acl-' + [guid]::NewGuid().ToString('N'))
$created = $false
try {
    New-Item -ItemType Directory -Path $scratch | Out-Null
    $created = $true
    $root = Join-Path $scratch 'evidence'
    $producer = @'
from pathlib import Path
import sys
sys.path.insert(0, "tools")
from run_offline_qa import REQUIRED, create_run, publish_manifest, verify_manifest
root = create_run(Path(sys.argv[1]))
for name in REQUIRED:
    (root / name).write_bytes(b"synthetic")
publish_manifest(root)
verify_manifest(root)
print(root.name)
'@
    $child = $producer | python - $root
    if ($LASTEXITCODE -ne 0 -or @($child).Count -ne 1 -or $child -notmatch '^offline-qa-[a-z0-9_]+$') {
        throw 'Synthetic QA producer failed'
    }
    $run = Join-Path $root $child
    $observations = @(
        Get-AclObservation $root 'root'
        Get-AclObservation $run 'run'
        foreach ($name in @('source-toolchain.json', 'code-audit.json', 'python-results.xml', 'summary.json', 'manifest.json')) {
            Get-AclObservation (Join-Path $run $name) $name
        }
    )
    # Positive detection control: change only this separate, disposable probe.
    $probe = Join-Path $scratch 'broad-read-probe'
    New-Item -ItemType Directory -Path $probe | Out-Null
    $acl = Get-Acl -LiteralPath $probe
    $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
        [System.Security.Principal.SecurityIdentifier]::new('S-1-1-0'),
        [System.Security.AccessControl.FileSystemRights]::ReadAndExecute,
        [System.Security.AccessControl.AccessControlType]::Allow)
    $acl.AddAccessRule($rule)
    Set-Acl -LiteralPath $probe -AclObject $acl
    $control = Get-AclObservation $probe 'positive-control'
    if ($control.broad_explicit_read_count -lt 1 -or $observations.Count -ne 7) {
        throw 'ACL observation control failed'
    }
    # Existing-root scenario: broad inheritable read on synthetic data only.
    $existing = Join-Path $scratch 'existing-evidence'
    New-Item -ItemType Directory -Path $existing | Out-Null
    $acl = Get-Acl -LiteralPath $existing
    $inheritable = [System.Security.AccessControl.FileSystemAccessRule]::new(
        [System.Security.Principal.SecurityIdentifier]::new('S-1-1-0'),
        [System.Security.AccessControl.FileSystemRights]::ReadAndExecute,
        [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
        [System.Security.AccessControl.PropagationFlags]::None,
        [System.Security.AccessControl.AccessControlType]::Allow)
    $acl.AddAccessRule($inheritable)
    Set-Acl -LiteralPath $existing -AclObject $acl
    $existingBefore = Get-AclObservation $existing 'existing-root-before'
    $existingChild = $producer | python - $existing
    if ($LASTEXITCODE -ne 0 -or @($existingChild).Count -ne 1 -or
        $existingChild -notmatch '^offline-qa-[a-z0-9_]+$') {
        throw 'Existing-root synthetic producer failed'
    }
    $existingRun = Join-Path $existing $existingChild
    $existingAfter = Get-AclObservation $existing 'existing-root-after'
    $existingEntries = @(
        $existingBefore
        $existingAfter
        Get-AclObservation $existingRun 'existing-run'
        foreach ($name in @('source-toolchain.json', 'code-audit.json', 'python-results.xml', 'summary.json', 'manifest.json')) {
            Get-AclObservation (Join-Path $existingRun $name) $name
        }
    )
    if ($existingBefore.broad_explicit_read_count -lt 1 -or
        $existingAfter.broad_explicit_read_count -lt 1 -or $existingEntries.Count -ne 8) {
        throw 'Existing-root observation control failed'
    }
    # Scoped regression contract for the qualified hosted Windows toolchain.
    # Do not confuse these selected ACE observations with effective access.
    $freshEntries = @($observations) + @($existingEntries | Select-Object -Skip 2)
    $unexpected = @($freshEntries | Where-Object {
        -not $_.canonical -or $_.broad_allow_count -ne 0 -or
        $_.owner_class -notin @('RUNNER', 'ADMINISTRATORS', 'SYSTEM')
    })
    if ($unexpected.Count -ne 0 -or -not $observations[0].protected -or
        -not $observations[1].protected -or -not $existingEntries[2].protected) {
        throw 'Scoped fresh-evidence DACL contract failed'
    }
    $report = [ordered]@{
        schema = 'windows-qa-acl-observation-v3'
        scope = 'SYNTHETIC_HOSTED_WINDOWS'
        observation = 'COMPLETE'
        positive_control = 'PASS'
        fresh_evidence_dacl_contract = 'PASS'
        effective_access = 'NOT_VERIFIED'
        hardware = 'NOT_RUN'
        entries = $observations
        existing_root_entries = $existingEntries
        control = $control
    }
    $stream = [System.IO.File]::Open($Output, [System.IO.FileMode]::CreateNew)
    try {
        $writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
        try { $writer.WriteLine(($report | ConvertTo-Json -Depth 6)) }
        finally { $writer.Dispose() }
    } finally { $stream.Dispose() }
    # The closed aggregate is safe for review without downloading raw ACLs.
    Write-Output ($report | ConvertTo-Json -Depth 6 -Compress)
    Write-Output 'PASS: scoped Windows DACL observation and positive control'
} catch {
    Write-Error 'FAIL: scoped Windows DACL observation' -ErrorAction Continue
    exit 1
} finally {
    if ($created) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}
