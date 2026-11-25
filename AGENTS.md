# AJAZZ Battery Tray — contributor instructions

Read [engineering standards](docs/engineering-standards.md), [adoption audit](docs/ENGINEERING_ADOPTION_AUDIT.md),
[architecture](ARCHITECTURE.md), [security](SECURITY.md), [roadmap](docs/ROADMAP.md)
and [resume](RESUME.md) before changes. The canonical roadmap is docs/ROADMAP.md;
the root ROADMAP.md is a pointer. Git is canonical. Universal portable policy
v1.0 is adopted through the adapted standard; unrelated source-project profile
and approvals are deliberately not copied to this public repository.

Inspect exact branch, HEAD/tree, working status, upstream and actual CI.
Do not overwrite concurrent changes. Use focused reviewable commits, tests,
documentation and explicit scoped evidence. No merge on failed/missing required
checks. Continue independent work; never bypass hardware, security or release gates.
Technical source/docs/diagnostics in English; localized UI EN/RU/UK.
Do not claim CI, synthetic fixtures or owner observations prove more than they do.

Preserve HID allowlists, explicit opt-ins, verified vs unverified separation,
legacy macOS support and existing CLI/API contracts. No speculative vendor writes,
firmware, automatic resets, destructive operations, raw captures, secrets,
publication or production changes without separate authorization.
Current release workflows are held fail-closed pending reviewed admission.
Do not dispatch releases or push release tags as part of ordinary development.
See the audit for outstanding implementation gaps; adoption does not imply PASS.
