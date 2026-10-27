# Recovering CI and candidate builds

Candidate builds and normal CI share Windows/Linux validation. Quality, non-UI
tests, UI tests, compilation, packaging, package verification, installer checks,
source materials and final delivery are separate jobs. No candidate workflow
creates a tag or release.

## Retry without changing code

Use **Re-run failed jobs** in Actions, or:

```sh
gh run rerun RUN_ID --failed
```

GitHub retains the original commit. Successful jobs and their checkpoints remain
available; the failed job and its dependent jobs run again. Work is recovered at
stage boundaries, not from an arbitrary command inside a job.

## Continue after fixing a failure

Commit and push the fix, then dispatch from the updated main:

```sh
gh workflow run candidates.yml --ref main \
  -f version=2.0.0 -f resume_run_id=PREVIOUS_RUN_ID
```

The standalone Windows/Linux build workflows accept the same inputs.
`force_rebuild=true` bypasses all reuse. Without an explicit resume run,
validation looks at the latest 20 completed main CI runs. A candidate waits for
CI already running on its commit instead of starting duplicate validation.

Each summary says **execute** or **reused**, shows the input fingerprint and
original producer. Changing only the installer test does not rebuild the app.
Changing application code, shipped resources or build dependencies invalidates
the corresponding runtime and its consumers. Unknown inputs invalidate reuse
conservatively. A failed assertion is never turned into a pass by retry policy.

## Retention, integrity and provenance

Intermediate checkpoints and their small sidecar receipts are retained for
7 days. Final candidates and matching source materials retain the existing
names/layout and last 30 days. A checkpoint is reusable only after its producing
job succeeds; an overall failed workflow may still contain successful stages.

Receipts identify exact inputs, environment, consumed files, SHA-256 values,
repository, source commit, run and attempt. The resolver checks receipts before
downloading large binaries. Payload checksums are verified before extraction;
Linux TARs preserve executable permissions and relative symlinks. PRs and the
tiny transport selftest cannot supply reusable results to main builds.

CI and candidate stages pin Python 3.13.17. Compatibility includes the base
runner image (for example ubuntu22), architecture and Python version. The exact
host-image revision is recorded in the producer metadata but does not invalidate
otherwise compatible artifacts when GitHub rolls out a security refresh.

Version 2 candidate manifests distinguish the currently evaluated source from
the actual producers of reused files; version 1 manifests remain readable.
Final exports are immutable. Retrying a partially completed delivery verifies
and retains identical existing exports; differing files require a new run.

If a checkpoint expired or a runner failed before saving it, repeat that stage.
Dependency downloads are cached, but model-download tests always use a fresh
profile and repeat online/offline processing when that verification is required.

## Lightweight pipeline verification

The manual **Checkpoint transport selftest** runs focused recovery tests and
transfers tiny files between real Windows/Linux jobs. It never compiles Yagua
or exports a candidate. Its checkpoints cannot be reused by candidate builds.
