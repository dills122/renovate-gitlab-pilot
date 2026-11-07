# Ticket-first update lifecycle: stale MRs and superseded releases

Recommended design, 2026-11-06. Proposed behavior, not implemented or validated by this document.

## Context and recommendation

The workplace flow is planning → Jira work-item creation/reservation → execution. The reported policy requires a ticket key in the MR title and every commit. The earlier local lab demonstrated ticket creation before the first commit, retry reuse, and keyed squash/merge results. Workplace implementation details have not been inspected.

**Recommend one active Jira story and MR per repository/update scope, with immutable plan revisions underneath it.** A newer eligible patch within the approved scope can advance the existing story/MR. A material scope change requires separate authorization and usually a new story. A completed story is never reused for a later update cycle.

This is a proposed internal change-management policy. The organization's owners must define permitted scope changes, approval requirements, Jira transitions, and retention. It does not establish SOC 2 compliance.

## Native Renovate behavior versus coordinator responsibilities

Renovate can regenerate an existing update branch when a newer dependency version appears. Grouping and branch configuration affect whether updates share an MR. It normally cleans up obsolete bot branches/MRs, but protects branches with separate human commits. Amending a bot commit is not a safe way to preserve human edits. Branch names and MR titles participate in Renovate's identification of previous proposals. Closing an MR may suppress that update, while grouped proposals can be recreated. [R1,R2]

The coordinator owns Jira mapping, immutable plans, eligibility, retries, suppression records, and evidence reconciliation. The Dependency Dashboard, if enabled, is a Renovate summary/control surface; it is not the Jira record. Do not infer Jira completion from a dashboard checkbox or disappearance of an MR from discovery.

## Reuse and replacement policy

| Event | Recommended action |
| --- | --- |
| Same eligible target discovered again | Reuse the active plan, story, MR and backlink; perform no duplicate creation. |
| Newer patch in the same approved dependency group/release line | Create a new immutable plan revision, reuse story/MR, record old/new targets, regenerate changes, and require fresh validation. |
| Newer release still held by age, capacity or rollout policy | Record it as held without reserving another story. Do not supersede an eligible open MR merely because an ineligible release exists. Revalidate whether its current target remains acceptable. |
| Minor update | Reuse only if that minor line is explicitly within the story's authorized scope and needs no new migration/review category; otherwise create new work. |
| Major upgrade, migration, changed group membership, or higher-risk workflow | Hold for scope classification; normally create a separately authorized story and plan. A major update can coexist with a useful patch—do not automatically call the patch obsolete. |
| Original target merged before the newer plan executes | Reconcile actual base/MR state. Complete the old cycle according to its evidence gate and plan remaining work as a new cycle/story. |
| Target already applied by another change | Record the actual landed evidence. Cancel/mark redundant unless policy allows completion through that external change; never invent a bot merge. |
| Human edits, manual MR closure, or manually terminal Jira story | Hold for reconciliation. Preserve human work and respect the recorded rejection; do not automatically reopen or recreate. |
| Update withdrawn or no longer permitted | Block merging, record why, and close/cancel through policy after confirming actual branch/MR state. |
| MR simply old | Report owner/action needed. Do not equate elapsed age with supersession or success. Escalation time is an owner-configured threshold. |

A stable story summary can describe “Update the approved Angular patch group” while its description records the exact target history. The MR title should still describe the actual update and retain the Jira key.

## Identity and stored state

Separate four identities:

- **Scope:** platform/project ID, base branch, workflow category, dependency/group identity, approved release line and scope-policy version. This is the concurrency boundary, not a permanent ticket ID.
- **Change cycle:** a unique durable ID for one active unit of work in that scope. Map it to one Jira story and the actual MR/branch. A later post-merge cycle gets a new ID.
- **Plan revision:** immutable plan ID/hash with exact versions/digests, group members, base SHA, policy and worker/tool versions, expected paths, validation profile and optional campaign/cohort. Superseding a plan preserves its record.
- **Execution attempt:** a retry/run ID referencing an existing plan revision; retries must not mint a new cycle.

Persist reservation status, Jira key, MR IID/URL, active plan revision, expected head SHA, transition history and evidence. Use one distributed-safe serialization mechanism per scope; a host-local lock is insufficient for writers on multiple hosts. A conditional active-revision update prevents an old executor from proceeding after a newer plan is admitted.

The early pilot's group+target-version reservation approach must be adapted before enabling story reuse across target versions. Adding a new version to a discovery report must not automatically create another story. This document does not claim that migration has been implemented.

## Processing sequence

1. **Reconcile first.** Read durable state plus current GitLab/Jira state. Identify merged, closed, human-modified, suppressed or ambiguous work before selecting a target. Lookup errors are unknown state, not “no existing work.”
2. **Plan eligibility.** Apply release age, compatibility, suppression, risk and cohort gates. Choose an exact target and scope action: reuse, replace, coexist or hold. Save a new immutable revision when the target/base/policy changes.
3. **Reserve or reuse Jira.** Under scope serialization, persist intent before creation. Use a stable cycle marker and idempotent backlink identity. After an uncertain create response, reconcile by marker; never blindly issue a second create. Multiple matches require operator resolution.
4. **Activate the revision.** Ensure the story exists and accurately describes the new scope/target before source changes. Supersede the old plan, block its execution, and invalidate its review eligibility. If required Jira synchronization fails, hold the update.
5. **Execute the exact plan.** Recheck base SHA, active revision, story state and MR state immediately before writes. Constrain Renovate to the selected targets. A registry change must not silently widen the plan. Restrict the run so it cannot modify unrelated ticketed branches through general maintenance or stale-branch pruning.
6. **Verify and reconcile output.** Check actual files, versions, MR title and every commit against the plan/key. Bind CI and advisory review to the actual head. Repair a missing backlink idempotently. A failed verification leaves work blocked, not completed.
7. **Merge and finish.** GitLab enforces required jobs and independent approvals. Verify landed squash/merge commits contain the key and record final SHAs. Use a “merged / awaiting verification” state if post-merge CI is required. Transition Jira to completion only after the agreed completion gate passes.

GitLab approval settings include removal of approvals after changes, but exact behavior and availability must be demonstrated on the workplace instance. Independently invalidate coordinator evidence whenever head, base or plan changes. An advisory report cannot enforce merge restrictions. [R3]

## Replacement, cancellation and race recovery

For a truly superseding change, create/link the replacement story and plan, then retire the obsolete bot-owned MR and transition its story to the mapped superseded/cancelled outcome. Preserve old links and targets. If replacement creation fails, keep the old work recorded and blocked as appropriate; do not lose it through eager cleanup.

There is no atomic transaction across Jira, GitLab and the state store. Persist each operation's intent/result and reconcile after failures. If a human merges while the coordinator is superseding an MR, the actual merge takes precedence: retain its landed evidence and recalculate remaining work from the new base. Cancellation alone is not proof that an old worker stopped; use active-revision checks and serialize writers through branch updates.

Use a reconciliation pass after writes and on a schedule to identify orphan reservations, MRs without mappings, missing backlinks, completed stories with open MRs, and superseded plans still executing. Unknown/ambiguous cases should hold with an operator action, not allocate fresh tickets.

Manual rejection requires an explicit suppression record specifying repository, package/group, rejected version or release line, reason, owner and optional expiry. Test how that record interacts with Renovate's closed-MR detection and `recreateWhen`; do not rely on manual title edits or blanket recreation settings. [R2]

## Example: shared APM skills

Illustrative cycle `skills-cycle-17` has story `CHANGE-123` and an MR for skills `v1.3.0`. Before merge, `v1.3.1` becomes eligible. Planning saves revision 2 with its exact commit and APM outputs, reuses `CHANGE-123`, and marks revision 1 superseded. Execution refreshes the same MR and lockfile; all generated commits keep the key. CI and skill checks run again. If `v1.3.0` merged meanwhile, revision 2 is stale and a new cycle must be planned instead.

A breaking skills release that changes hooks, permissions or instruction behavior is not automatically routine work just because its version looks like a patch. Classification can require a new review category and separate story.

## Local acceptance tests

| Test | Pass condition |
| --- | --- |
| Release B after an open MR for A | Same-scope B gets one new plan revision, same story/MR, correct key on every commit and fresh CI/review evidence. |
| B is too young | No B story or executable plan; A remains unchanged unless separately disallowed. |
| Concurrent discovery and retry | One active cycle/story/MR; old revision cannot write after replacement is activated. |
| Jira timeout after creation | Reconciliation adopts the existing story; no duplicate create or backlink. |
| Base moves or A merges during planning | Stale execution is refused; next cycle reflects actual landed state. |
| Human commit or manual closure | No lost work and no unauthorized recreation; explicit hold/suppression outcome. |
| Material scope change | Separate authorization and correctly linked work; old patch retained if still useful. |
| Crash after MR creation, before Jira link | Retry repairs the link using the saved cycle without duplicating work. |
| Approval then target update | Previous review evidence cannot authorize the new head; trusted merge controls require current evidence. |
| Squash merge and delayed Jira update | Landed keys/SHAs verified; retry completes the same story transition without new work. |

## Sources and open decisions

Official living documentation reviewed 2026-11-06:

- R1. [Renovate branch updates and rebasing](https://docs.renovatebot.com/updating-rebasing/).
- R2. [Renovate MR identification, closed proposals and abandoned branches](https://docs.renovatebot.com/key-concepts/pull-requests/).
- R3. [GitLab approval settings](https://docs.gitlab.com/user/project/merge_requests/approvals/settings/).

Before implementation, map conceptual states to available Jira transition IDs; confirm permitted story-scope changes, what “done” means, GitLab tier/settings, the deployed Renovate version, branch/title templates, persistent-state capabilities and writer isolation. No exact workplace Jira statuses or transition IDs are assumed. Retain the existing human approval requirement and report-only reviewer until a separate policy decision changes them.
