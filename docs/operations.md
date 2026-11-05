# Run the pilot and decide whether to expand

## Read-only acceptance

1. Record the repo owner, feed owner, Jira owner and operational contact. Use one non-production workspace with a real private dependency and a known eligible Angular or Nx patch. Confirm exact pins, actual group manifests/sections and required CI job names. A single package missing from a configured group excludes that whole group.
2. Run `discover-patches` on protected main. Download `patch-candidates.json`. Check the repo/project ID, base SHA, group membership, candidate versions and selection. Zero candidates with no eligible patch is a successful no-op. Missing manifest/group, private package lookup failure, or a Renovate report problem should fail the job. No Jira credentials are required here.
3. Have app CI do a frozen install on a clean runner with an empty pnpm store. Run real build/typecheck/tests. Adapt [target CI example](../examples/target-ci.yml) to the workspace's actual targets; ensure the target workflow creates an MR pipeline, not just a branch pipeline. Verify all required jobs run and none allow failure. Remove feed access in a sandbox negative test and confirm neither worker silently succeeds via a public fallback. Inspect traces for credentials before sharing.
4. Confirm the pinned Renovate version, package toolchain, corporate CA, private tarball URLs and target CI behavior with the app team. Keep the repo allowlist at one until the evidence is accepted.

## First write

1. Confirm a mount at `/var/lib/renovate-reservations`, its marker, backup owner and restore procedure. Enable `PILOT_WRITE_ENABLED=true` for the protected writer environment.
2. In the same pipeline play **ticket-first**. If main changed, start a new pipeline. Record the returned Story key, MR IID, SHA and commit list. The Story must already exist before the first bot commit. Confirm both packages and the lockfile updated together. Check every commit, even when the MR has more than one.
3. Retry the writer in the same pipeline. Expect the same Story, MR and one backlink. Independently search Jira for the reservation label. Pause if the result is ambiguous. A later pipeline may legitimately select another eligible group.
4. When target CI finishes, play **review-mr**. Save its decision, MR, SHA and pipeline ID. If target main or the bot head changed, refresh discovery and the writer result; an old report is historical evidence.
5. Try merging with zero approvals, a missing ticket, a failing pipeline, and a new bot head after approval. Record what actually blocks each attempt. If the internal policy mandates a verified ticket to merge, configure an **independent, trusted required control** and demonstrate denial before rollout. A manual advisory report alone cannot enforce it.
6. Have an eligible human approve the legitimate MR. Squash-merge it and compare the previous main SHA with the new head. Verify the key in every introduced commit and the final main pipeline. The expected human approval count and retention period come from your policy owner.
7. Save the Jira key, MR URL, automation pipeline and job IDs, required test pipeline and SHA, human approval record and landed SHAs. The pilot artifact lifetime is seven days; plan durable retention separately.

## Recovery and pause

| Symptom | Action |
| --- | --- |
| Feed metadata works but lockfile or CI install fails | Check tarball host/path permissions, CA, pnpm version and the target repo's npmrc. Repeat with an empty store. |
| Jira creation timed out or a pending reservation has no visible Story | Keep the writer stopped for that group. Search the Jira project by the exact label, account for search delay, inspect Jira audit logs and state with the owner. If the issue exists with the correct label, retry to adopt it. If absence is verified, back up the DB with writes paused, then have the operator clear only that confirmed pending row before retry. Never blindly retry a Jira create after an uncertain response. |
| MR created, backlink failed | Fix Jira connectivity or permissions, rerun the same writer. It uses the same selected group, saved key and link global ID. |
| Worker restarted or state disk unavailable | Restore the backed-up DB and marker on the designated writer volume; reconcile open MRs and Jira labels before enabling writes. Do not recreate a blank marker as a shortcut. |
| Incoming patch changes or existing MR contains human work | Hold and inspect. Reserve the branch prefix for the bot. Do not rebase human-owned branches automatically. Start a fresh pipeline for a different target SHA. |
| Need to stop | Unset the writer enable variable and disable schedules. Cancel active writers, revoke machine tokens if necessary, and preserve reservations and evidence. Existing MRs stay reviewable. |

**Ownership.** Platform owns runner/image rotation, secret injection, backup/restore and incident response. App owners own group boundaries and tests. Jira owners own fields and machine permissions. GitLab/change-control owners own approval, retention and squash policy. Start with manual jobs; later make only the read job automatic for scheduled pipelines by changing its rules after the pilot is accepted.

**Budget boundary.** One repo, one known patch, one real private package, one test Jira project. The provided selection expects exact semantic-version pins in one configured manifest per group. Workspaces with ranges, catalogs, peer-only updates or several registries need additional policy and testing. The reviewer validates files, package pins and required CI; it does not audit all transitive lockfile content. Keep existing dependency scanning and human review.

For the landed-history check, fetch the target into a trusted checkout and run `python3 /path/to/automation/scripts/check-landed.py BEFORE_MAIN_SHA AFTER_MAIN_SHA APP-123` from that checkout. Use the SHAs immediately surrounding that one merge. It exits unsuccessfully for an empty range, unrelated history or any newly reachable commit whose subject lacks the exact key prefix.
