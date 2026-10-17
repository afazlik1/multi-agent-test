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

## Branch-history cleanup completed

All four published branch histories have been rewritten with a generic author/committer identity and UTC timestamps. Historical host fingerprints, private paths in diagnostics, generated execution files, and local request text were removed. The original development/experiment commits and branching structure were preserved. Commit references in reports, JSON/CSV artifacts, and SQLite records were updated to their rewritten counterparts, with benchmark source snapshots and evaluation trajectories unchanged.

The owner explicitly authorized this one-time rewrite. Remote replacement used exact branch-head leases; ordinary publication continues to prohibit force-pushing. Other clones must be re-cloned or carefully migrated to avoid reintroducing the original history. The private rollback copy is excluded from publication.

## Remaining hosting-provider cleanup before public release

**Rewriting branches does not guarantee deletion of GitHub caches or PR references.** Three pre-existing PRs reference affected history. Post-rewrite verification confirmed that the three PR head refs follow the sanitized branches, but the three old PR merge refs remain advertised. An authenticated GitHub API request still returned an old commit containing identifying author metadata. Hosting-provider removal is therefore still outstanding; branch anonymization alone has not purged all hosted copies. The owner-authorized request was submitted to GitHub Support; its receipt and confirmation screenshot are retained privately, outside version control. Cleanup has not yet been confirmed. Repository visibility remains private. The owner-authorized support request has now been submitted and is awaiting review. Repository visibility is unchanged.

See [GitHub's sensitive-data removal documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). The provider decides whether a removal request meets its sensitive-data criteria.

Local-only application snapshots and private audit output are not published by normal branch pushes and are outside the public-release export. Existing clones must be handled separately if history is rewritten. Pattern-based checks reduce exposure but do not establish that every possible credential or identifying detail has been detected.

## Validation

All 25 automated tests pass, including privacy redaction, restricted execution, exact evaluation budgets, restart recovery, and replay of the original recorded trajectories. No new hidden-objective optimization evaluations were used for the privacy cleanup.
