# Privacy review before public release

## Completed cleanup

- Removed the recorded host operating-system version and CPU architecture from `experiments/environment.json`; software versions needed for reproducibility remain.
- Removed generated worker launchers and sandbox profiles from the current versions of all three worker branches. These files embedded machine-specific home-directory and dependency paths.
- Redacted local paths in a saved worker failure report while preserving the failure diagnosis.
- Added path redaction before persisting future structured diagnostics and before returning worker traceback errors.
- Added cleanup of generated execution files and ignore rules for those files, local request text, local environment files, and common private-key files.
- Replaced the repository-local Git author/committer defaults with a generic contributor identity. Global Git settings were not changed.
- Sanitized hardware specifications in the local request file, which is excluded from publication.

## Scope and findings

The review covered current main and worker branch files, Git object history and commit metadata, JSON/CSV experiment artifacts, both SQLite experiment databases, PNG metadata, and GitHub repository/PR/issue/release/workflow metadata.

No credential-pattern matches were found in scanned reachable Git blobs. No personal image metadata was found. Both experiment databases passed integrity checks; optimization metrics were preserved. At review time GitHub had three open PRs with no bodies, comments, or submitted reviews, no workflow runs, and no releases.

Generic operating-system requirements and local service addresses are retained because they describe how the framework works rather than identifying a particular computer. Repository ownership and account information remain visible through the hosting platform.

## Outstanding before making the repository public

**Current-file cleanup does not erase history.** Earlier commits retain real author names, a hostname-derived email, host platform metadata, and local paths. Three GitHub-managed PR refs also retain affected history. Repository visibility remains private.

The original project instructions prohibit force-pushing. A separate approval is required to rewrite/anonymize all four published branch histories and replace their remote refs. That operation changes commit IDs and requires coordinating existing worktrees, experiment provenance references, and the three PRs. GitHub-managed cached views and PR refs may need hosting-provider cleanup; rewriting branches alone is not a complete guarantee.

See [GitHub's sensitive-data removal documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). The provider decides whether a removal request meets its sensitive-data criteria.

Local-only application snapshots and private audit output are not published by normal branch pushes and are outside the public-release export. Existing clones must be handled separately if history is rewritten. Pattern-based checks reduce exposure but do not establish that every possible credential or identifying detail has been detected.

## Validation

All 25 automated tests pass, including privacy redaction, restricted execution, exact evaluation budgets, restart recovery, and replay of the original recorded trajectories. No new hidden-objective optimization evaluations were used for the privacy cleanup.
