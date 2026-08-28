$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$expectedParent = '74780b65dcf9954bdf915aecbf57cd17fd6b43ea'
$manifestRelative = 'release/github/2026-08-28-integrated-final/github-explicit-paths-integrated-final.json'

$head = (& git -C $projectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -ne $expectedParent) {
    throw "Unexpected local parent: $head"
}

$qaPlanPath = Join-Path $projectRoot 'qa\INTEGRATED_RIGHTS_RELEASE_QA.json'
$qaPlan = Get-Content -LiteralPath $qaPlanPath -Raw | ConvertFrom-Json
if ($qaPlan.result -ne 'pass' -or -not $qaPlan.release_ready) {
    throw 'The integrated rights/release audit is not release-ready.'
}

$frozenInputPath = Join-Path $projectRoot 'release\zenodo\2026-08-28-integrated-final\release-inputs-integrated.json'
$frozenInputs = Get-Content -LiteralPath $frozenInputPath -Raw | ConvertFrom-Json
if (-not $frozenInputs.frozen) { throw 'The integrated release input set is not frozen.' }
foreach ($property in $frozenInputs.artifacts.PSObject.Properties) {
    $entry = $property.Value
    $artifactPath = Join-Path $projectRoot ([string]$entry.path -replace '/', '\')
    if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) {
        throw "Frozen artifact is missing: $($entry.path)"
    }
    $item = Get-Item -LiteralPath $artifactPath
    $digest = (Get-FileHash -LiteralPath $artifactPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.Length -ne [long]$entry.bytes -or $digest -ne [string]$entry.sha256) {
        throw "Frozen artifact identity mismatch: $($entry.path)"
    }
}

# Build the release commit in a dedicated index seeded from the exact parent.
# This prevents any pre-existing staged work in the ordinary repository index
# from entering the bounded publication commit.
$indexPath = Join-Path $PSScriptRoot 'github-integrated-final.index'
if (Test-Path -LiteralPath $indexPath) {
    Remove-Item -LiteralPath $indexPath -Force
}
$env:GIT_INDEX_FILE = $indexPath
& git -C $projectRoot read-tree $expectedParent
if ($LASTEXITCODE -ne 0) { throw 'Failed to seed the isolated release index.' }

$candidates = [System.Collections.Generic.List[string]]::new()
foreach ($relative in $qaPlan.recommended_release_file_plan.github_reader_first_commit_paths) {
    $candidates.Add([string]$relative)
}

$extras = @(
    '00_control/BUILD_AND_QA.md',
    '00_control/CURRENT_CURSOR.md',
    '00_control/CURRENT_GOAL_AND_WORKFLOW.md',
    '00_control/CURRENT_STATE.md',
    '00_control/DECISION_LOG.md',
    '00_control/PUBLICATION_RECEIPTS.md',
    'PROVENANCE.md',
    'RIGHTS.md',
    'source/id-ID/o015-accessibility-id.tex',
    'source/id-ID/latex-lab-testphase-latest.sty',
    'source/id-ID/macros-id.tex',
    'source/id-ID/figures/discontinuous_function.png',
    'source/id-ID/figures/lsc_function.png',
    'source/id-ID/figures/sets.png',
    'source/id-ID/figures/balls.png',
    'source/id-ID/figures/convex_fct.png',
    'source/id-ID/figures/gradient.png',
    'source/id-ID/figures/subgradient.png',
    'qa/build_integrated_pdf.py',
    'qa/build_integrated_readers.py',
    'qa/extend_backend_original_03.py',
    'qa/validate_backend_original_03.py',
    'qa/verify_integrated_pdf.py',
    'qa/verify_integrated_readers.py',
    'qa/verify_integrated_reflow_independent.py',
    'qa/verify_original_03_course_closure.py',
    'qa/INTEGRATED_RIGHTS_RELEASE_QA.json',
    'release/github/2026-08-28-integrated-final/prepare_github_integrated_final.ps1',
    'release/github/2026-08-28-integrated-final/verify_github_integrated_final_public.py'
)
foreach ($relative in $extras) { $candidates.Add($relative) }

$releaseFiles = @(
    'release/final/2026-08-28/ADVANCED_OPTIMIZATION_CONVEX_ANALYSIS_ID_INTEGRATED_RELEASE_2026.08.28.zip',
    'release/final/2026-08-28/local-verification-integrated.json',
    'release/final/2026-08-28/prepare_integrated_release.py',
    'release/final/2026-08-28/release-manifest-integrated-zenodo.json',
    'release/final/2026-08-28/RIGHTS_AND_PROVENANCE_INTEGRATED.md',
    'release/final/2026-08-28/SHA256SUMS-integrated',
    'release/zenodo/2026-08-28-integrated-final/metadata-integrated.template.json',
    'release/zenodo/2026-08-28-integrated-final/publish_integrated_final.py',
    'release/zenodo/2026-08-28-integrated-final/release-inputs-integrated.json',
    'release/zenodo/2026-08-28-integrated-final/release-inputs-integrated.template.json',
    'release/zenodo/2026-08-28-integrated-final/RIGHTS_AND_PROVENANCE_INTEGRATED.template.md'
)
foreach ($relative in $releaseFiles) { $candidates.Add($relative) }

$candidatePaths = @($candidates | Sort-Object -Unique)
foreach ($relative in $candidatePaths) {
    if ($relative -match '(^|/)\.\.?(/|$)' -or $relative -match '^[A-Za-z]:' -or $relative.StartsWith(':')) {
        throw "Unsafe candidate path: $relative"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot ($relative -replace '/', '\')) -PathType Leaf)) {
        throw "Missing candidate path: $relative"
    }
}

& git -C $projectRoot --literal-pathspecs add -- $candidatePaths
if ($LASTEXITCODE -ne 0) { throw 'git add failed' }

$stagedBeforeManifest = @(
    & git -C $projectRoot --literal-pathspecs diff --cached --name-only -- $candidatePaths |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ }
)
if ($LASTEXITCODE -ne 0 -or $stagedBeforeManifest.Count -eq 0) {
    throw 'No bounded staged changes were found.'
}

$expectedPaths = @($stagedBeforeManifest + $manifestRelative | Sort-Object -Unique)
$manifest = [ordered]@{
    schema = 'o015-github-integrated-final-explicit-paths-v1'
    repository = [ordered]@{
        owner = 'KokunoYumeto'
        name = 'advanced-optimization-convex-analysis-id'
        branch = 'main'
    }
    release = 'integrated-course-final-2026.08.28'
    expected_parent = $expectedParent
    required_path_count = $expectedPaths.Count
    path_groups = [ordered]@{
        release_commit_paths = $expectedPaths
    }
    post_commit_receipt = 'release/github/2026-08-28-integrated-final/github-public-readback-integrated-final.json'
    intentional_exclusions = @(
        'credentials and authenticated request material',
        'temporary, cache, rendered-scratch, and __pycache__ paths',
        'the post-commit readback receipt, generated only after the commit exists',
        'unrelated task files and broad workspace state'
    )
}
$manifestPath = Join-Path $projectRoot ($manifestRelative -replace '/', '\')
$manifestJson = $manifest | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($manifestPath, $manifestJson + "`n", [System.Text.UTF8Encoding]::new($false))

& git -C $projectRoot --literal-pathspecs add -- $manifestRelative
if ($LASTEXITCODE -ne 0) { throw 'git add of explicit manifest failed' }

$actualPaths = @(
    & git -C $projectRoot --literal-pathspecs diff --cached --name-only -- $expectedPaths |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ }
)
if ($LASTEXITCODE -ne 0 -or (Compare-Object -ReferenceObject $expectedPaths -DifferenceObject $actualPaths)) {
    throw 'Final staged path set does not equal the explicit manifest.'
}
$statuses = @(& git -C $projectRoot --literal-pathspecs diff --cached --name-status --no-renames -- $expectedPaths)
$unexpectedStatuses = @($statuses | Where-Object { $_ -notmatch '^[AM]\s' })
if ($LASTEXITCODE -ne 0 -or $unexpectedStatuses.Count -ne 0) {
    throw 'Final staged change contains a status other than added or modified.'
}

[ordered]@{
    result = 'pass'
    parent = $head
    candidate_path_count = $candidatePaths.Count
    staged_path_count = $actualPaths.Count
    only_added_or_modified = $true
    explicit_manifest = $manifestRelative
    isolated_index = $indexPath
} | ConvertTo-Json -Depth 5
