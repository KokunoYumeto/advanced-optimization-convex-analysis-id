$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$expectedParent = 'b57225d46631680b3755edcd23975916e84a8b6c'
$manifestRelative = 'release/github/2026-08-28-integrated-final/github-explicit-paths-integrated-final-evidence.json'
$indexPath = Join-Path $PSScriptRoot 'github-integrated-final-evidence.index'

$head = (& git -C $projectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -ne $expectedParent) {
    throw "Unexpected local parent: $head"
}

$boundReceipts = @(
    [ordered]@{
        path = 'release/github/2026-08-28-integrated-final/github-public-readback-integrated-final.json'
        bytes = 18904
        sha256 = 'f411b3d3fbb244526cf7d4b4993bc4f446c24676c787ac800d2c9926a80a4b19'
    },
    [ordered]@{
        path = 'release/zenodo/2026-08-28-integrated-final/zenodo-public-readback-integrated.json'
        bytes = 27343
        sha256 = 'e5f75072c2d0aa6f2bfdfaa0a620495d913f75644528a626197089d183fcf176'
    },
    [ordered]@{
        path = 'release/zenodo/2026-08-28-integrated-final/zenodo-draft-closure-integrated.json'
        bytes = 475
        sha256 = '7907a1b6109a664e75aec5d55f3f3ab9d9b64b827d84304eebb59d81098ab437'
    },
    [ordered]@{
        path = 'qa/INTEGRATED_TERMINAL_PUBLICATION_AUDIT.json'
        bytes = 1863
        sha256 = 'c17677c7de0806080f41f98f6e38bc0f817fc6d06fc27b644021462bdf24c3d3'
    }
)
foreach ($entry in $boundReceipts) {
    $path = Join-Path $projectRoot ($entry.path -replace '/', '\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing bound evidence: $($entry.path)"
    }
    $bytes = (Get-Item -LiteralPath $path).Length
    $sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bytes -ne [long]$entry.bytes -or $sha256 -ne $entry.sha256) {
        throw "Bound evidence identity mismatch: $($entry.path)"
    }
}

if (Test-Path -LiteralPath $indexPath) {
    Remove-Item -LiteralPath $indexPath -Force
}
$env:GIT_INDEX_FILE = $indexPath
& git -C $projectRoot read-tree $expectedParent
if ($LASTEXITCODE -ne 0) { throw 'Failed to seed isolated evidence index.' }

$candidates = @(
    'README.md',
    '00_control/BUILD_AND_QA.md',
    '00_control/CURRENT_CURSOR.md',
    '00_control/CURRENT_GOAL_AND_WORKFLOW.md',
    '00_control/CURRENT_STATE.md',
    '00_control/DECISION_LOG.md',
    '00_control/PUBLICATION_RECEIPTS.md',
    '00_control/SOURCE_AUTHORITY.json',
    'qa/INTEGRATED_TERMINAL_PUBLICATION_AUDIT.json',
    'qa/verify_integrated_terminal_publication.py',
    'release/github/2026-08-28-integrated-final/github-public-readback-integrated-final.json',
    'release/github/2026-08-28-integrated-final/prepare_github_integrated_final_evidence.ps1',
    'release/github/2026-08-28-integrated-final/verify_github_integrated_final_evidence_public.py',
    'release/zenodo/2026-08-28-integrated-final/publish_integrated_final.py',
    'release/zenodo/2026-08-28-integrated-final/zenodo-draft-closure-integrated.json',
    'release/zenodo/2026-08-28-integrated-final/zenodo-draft-integrated.json',
    'release/zenodo/2026-08-28-integrated-final/zenodo-public-readback-integrated.json'
)
foreach ($relative in $candidates) {
    if ($relative.StartsWith(':') -or $relative -match '(^|/)\.\.?(/|$)' -or $relative -match '^[A-Za-z]:') {
        throw "Unsafe candidate path: $relative"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot ($relative -replace '/', '\')) -PathType Leaf)) {
        throw "Missing candidate path: $relative"
    }
}

& git -C $projectRoot --literal-pathspecs add -- $candidates
if ($LASTEXITCODE -ne 0) { throw 'Bounded evidence staging failed.' }
$staged = @(
    & git -C $projectRoot --literal-pathspecs diff --cached --name-only -- $candidates |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ }
)
if ($LASTEXITCODE -ne 0 -or $staged.Count -eq 0) { throw 'No evidence changes were staged.' }

$expectedPaths = @($staged + $manifestRelative | Sort-Object -Unique)
$manifest = [ordered]@{
    schema = 'o015-github-integrated-final-evidence-explicit-paths-v1'
    repository = [ordered]@{ owner = 'KokunoYumeto'; name = 'advanced-optimization-convex-analysis-id'; branch = 'main' }
    release = 'integrated-course-final-evidence-2026.08.28'
    expected_parent = $expectedParent
    required_path_count = $expectedPaths.Count
    path_groups = [ordered]@{ evidence_commit_paths = $expectedPaths }
    post_commit_receipt = 'release/github/2026-08-28-integrated-final/github-public-readback-integrated-final-evidence.json'
}
$manifestPath = Join-Path $projectRoot ($manifestRelative -replace '/', '\')
[System.IO.File]::WriteAllText(
    $manifestPath,
    ($manifest | ConvertTo-Json -Depth 10) + "`n",
    [System.Text.UTF8Encoding]::new($false)
)
& git -C $projectRoot --literal-pathspecs add -- $manifestRelative
if ($LASTEXITCODE -ne 0) { throw 'Evidence-manifest staging failed.' }

$actual = @(
    & git -C $projectRoot --literal-pathspecs diff --cached --name-only -- $expectedPaths |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ }
)
$statuses = @(& git -C $projectRoot --literal-pathspecs diff --cached --name-status --no-renames -- $expectedPaths)
$unexpected = @($statuses | Where-Object { $_ -notmatch '^[AM]\s' })
$pathDifference = @(Compare-Object -ReferenceObject $expectedPaths -DifferenceObject $actual)
if ($LASTEXITCODE -ne 0 -or $pathDifference.Count -ne 0 -or $unexpected.Count -ne 0) {
    throw 'Isolated evidence index does not equal its explicit A/M manifest.'
}

[ordered]@{
    result = 'pass'
    parent = $head
    staged_path_count = $actual.Count
    explicit_manifest = $manifestRelative
    isolated_index = $indexPath
} | ConvertTo-Json -Depth 5
