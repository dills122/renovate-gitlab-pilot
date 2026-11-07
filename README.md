# Ticket-first Renovate pilot for work

Copy **the contents of this directory**, including the dotfiles, into a private work GitLab project such as `platform/renovate-automation`. This is the portable starter. The Research Depot experiments, local Docker Compose stack, and personal Jira site stay in the research repo. Nothing in this kit needs the Mac lab.

Start with the [workplace handoff and owner requests](docs/handoff.md). For expansion beyond the initial workspace, see the [enterprise feature experiments](docs/feature-roadmap.md) and [polyrepo workflows and APM shared-skills rollout plan](docs/polyrepo-workflows.md). The latter includes four proposed local experiments covering JVM baselines, CI templates, canary/retry behavior, and Agent Package Manager skills releases.

The first milestone is a read-only pipeline that uses the work runner to discover eligible Angular and Nx patches in one approved sandbox. Enable Jira and GitLab writes only after private feed access and target CI work. Start with manual jobs and independent human approvals.

## What happens in a pipeline

1. **discover-patches** reads the protected config, records the target SHA, tests an authenticated lookup of one private npm package, then runs Renovate in lookup mode. It saves the candidates and one selection to `patch-candidates.json`.
2. **ticket-first** consumes that artifact in the same pipeline. It rejects a stale SHA or policy, checks the target package pins and writer identity, then reserves a Story in the configured Jira project. It gives the verified key and selected patch to Renovate. After the push it checks the MR title and every MR commit, upserts the Jira backlink, and saves the result artifact. Retrying the same pipeline uses the same selection and reservation. An empty selection exits without contacting Jira.
3. **review-mr** is a manual, read-only report. Play it after the target MR pipeline finishes. It examines the current SHA, expected package edits, file list, all commits, mandatory jobs, Story and backlink. It returns HOLD when evidence is missing. GitLab enforces merge permissions separately. The report never approves or merges.

## Setup order

| Step | Action and exit criterion |
| --- | --- |
| 1. Pick a sandbox | App owner supplies one non-production pnpm/Nx workspace, the Angular and Nx pins and manifest paths, an internal package for the feed test, expected build/test jobs, and an example ticketed squash merge. Use a repo with no pre-existing dependency MRs for the selected groups on the first run. |
| 2. Create the automation project | Platform team creates a private GitLab project, protects the default branch and restricts changes to the automation code, policy and CI. Disable unrelated group/instance runners and restrict ad hoc pipeline variable overrides. Give approved maintainers permission to play manual jobs. |
| 3. Configure the pilot | Copy `pilot.example.json` to `pilot.json` in the automation repo. Replace all example values; commit this **non-secret** config to the work repo through its normal review process. Each named group currently expects exact numeric pins, in one manifest and dependency section. Pick a workspace and group scope where the configured package list is complete. Use the repo's actual job names, base branch and workspace lockfile path. |
| 4. Build and register | Use the [runner and image guide](docs/runners.md) to build the image, store it in the approved registry, register the restricted runners, provision the writer volume, and set `PILOT_IMAGE` to a digest. |
| 5. Supply identities | Use the [access table](docs/access.md) for environment scopes, Azure credentials, Jira Cloud/Data Center settings, target CI access and protected branch rules. The automation project's tokens do not go into application repos. |
| 6. Run the read-only gate | Run the local checks below, then use **Build → Pipelines → New pipeline** on protected main and play **discover-patches**. Verify the selected version and target SHA. Separately verify a cold frozen install and the real application tests from target CI through the private feed. |
| 7. Exercise one write and merge | Follow [acceptance, recovery and rollback](docs/operations.md). Set the protected writer enable flag only after steps 1–6. Keep the reviewer advisory and obtain independent human approval. |

## Local checks

Python 3.10+ and its standard library are sufficient for these offline checks:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
sh -n scripts/register-runner.sh
sh -n scripts/setup-state.sh
```

The automation jobs also require Git, Renovate and pnpm. The supplied Dockerfile pins the Renovate 44.216.2 base and pnpm 10.23.0 package by digest/checksum, matching the lab. Set the workplace pnpm version and verify its new tarball checksum if different. Revalidate lookup report parsing on every Renovate upgrade; the report file interface is experimental. [Renovate report configuration](https://docs.renovatebot.com/self-hosted-configuration/#reporttype)

## Where things live

| Location | Contents |
| --- | --- |
| Private work automation repo (canonical) | This README, docs, Dockerfile, CI YAML, scripts, reviewed `pilot.json`, owner/on-call and recovery procedures. Put a link here from your internal wiki. |
| Target Angular/Nx repo | Non-secret registry routing, trusted required CI jobs, application tests, branch protection, human approval rules and commit message templates. |
| Approved image registry | Immutable worker image referenced by digest. Bootstrap its pull authorization on the runner. |
| Secret manager or protected GitLab variables | Runtime machine credentials, separated by job/environment. Keep raw tokens, authenticated npmrc files and registration tokens out of Git, images, artifacts and docs. |
| Persistent writer volume | SQLite Story reservation database and volume marker. Use a single writer host for this pilot, with backups and a named owner. |
| GitLab and Jira | MR/commits, pipelines, human approvals, Story and backlink. Store or export evidence per the organization's retention policy; the sample CI artifacts expire after seven days. |

The local lab proved fresh Story creation, grouped MR, reuse after retry and keyed commits after squash on GitLab EE 18.11.14 with Jira Cloud. This port adds workplace configuration, Azure feed access, persistent SQLite and a Data Center API option. Work-specific network access, Jira fields/permissions, runner isolation, approval enforcement and SLA remain pilot acceptance tests.
