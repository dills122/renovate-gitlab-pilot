# Renovate beyond application dependency bumps

Date: 2026-11-06. Status: researched; experiments proposed, not executed.

## Decision and scope

Question: which additional workflows fit the existing workplace planning → Jira reservation → executor pipeline, particularly Kotlin/Gradle polyrepo alignment? Owner: the pilot lead with workplace platform/build owners.

The user reports that this workplace pipeline already creates ticketed dependency updates successfully. This is user-reported evidence, not an inspection of workplace code. Preserve that architecture and investigate extensions. This document covers public research and proposed experiments; it does not represent implemented workflow extensions.

Budget/stopping rule: one bounded research pass, stopping after first-party adoption examples, relevant official capability checks, and three falsifiable pilot proposals. Prefer practitioner accounts of their own systems and official Renovate/Gradle documentation. Rank candidates by repeated toil removed, fit with existing ticket controls, deterministic output, and ability to test in isolated repositories.

## Conclusion — recommendation

Use Renovate to distribute **versioned organizational standards**: JVM platforms, published build plugins, CI templates, internal libraries, container images, and shared agent skills distributed through APM (Agent Package Manager). Keep fleet policy, rollout sequencing, ticket identity, and evidence collection in the existing coordinator. Start with three synthetic Kotlin services and one shared baseline artifact. A successful individual MR does not establish fleet-wide compatibility.

## What others actually do

| Evidence | Published use | Relevance and limits |
| --- | --- | --- |
| Aircall [S25] | Custom regex manager discovers a GitLab runner chart version inside a custom Terraform module. Updates go to SRE runners before the wider fleet. | Direct precedent for infrastructure maintenance and staged adoption. Does not establish an automatic cross-repository promotion gate. |
| Nicolas Fränkel [S26] | Uses post-upgrade Gradle commands to regenerate dependency verification metadata/keyring files alongside updates. | Direct account of maintaining generated build artifacts. Current Renovate also has native verification support [S27]; test that before reproducing his custom command. |
| Jon Simeon [S28] | Uses a custom manager for image references in BlueBuild configuration in his own homelab. | Demonstrates adapting extraction to a proprietary/nonstandard format; personal usage, not enterprise-scale evidence. |
| Renovate maintainers [S29] | Document custom datasource examples for Grafana dashboard revisions and HTTP-served version inventories. | Official capability examples, not evidence of customer adoption. Useful for versioned internal standards outside package registries. |

Historical-source caveat: Fishbrain's 2023 Gradle catalog migration article concludes with Dependabot adoption and contains an old claim about Renovate/buildSrc. It is not counted as Renovate adoption evidence; current Renovate documentation includes buildSrc Kotlin patterns [S27].

## Candidate workflows

These are recommendations/inferences grounded in the cited capabilities, not claims that the workplace implementation already supports them.

| Priority | Workflow | What changes | Existing workflow extension and acceptance evidence |
| --- | --- | --- | --- |
| 1 | JVM baseline rollout | Shared platform/BOM or published catalog dependency in each service | Plan exact baseline release and consumer cohort. Compile, test, and inspect resolved dependency versions. Separate compatibility cohorts where required. [S27,S30,S31] |
| 1 | Gradle build-convention rollout | Version of an internally published Gradle plugin | Package repeatable compiler/test/lint configuration into a plugin first; Renovate can then update the plugin reference. Test plugin extraction, repository credentials, and affected build tasks. [S27,S32] |
| 1 | Shared GitLab CI template rollout | Versioned project include refs | Native gitlabci-include uses GitLab tags. Lint and run consumer pipelines; compare required jobs so a green pipeline cannot hide deleted tests. Existing floating refs need an initial deliberate pinning change. [S33] |
| 1 | Shared agent skills via APM | Versioned skills-package references and APM lockfile | Release-driven discovery, ticketed consumer MRs, frozen installation and skill-content checks; see the dedicated proposal below. [S37,S38] |
| 2 | Internal library/client propagation | Maven/npm/Python package release references | Producer releases feed consumer plans. Add API/contract tests and staged consumers. Generated clients should preferably be published packages; regeneration from schemas needs a separate task contract. [S27,S34] |
| 2 | Build/runtime image alignment | Dockerfile and CI image tags/digests | Track approved image families and tested releases, then roll out to canaries. Image update does not itself prove JDK/compiler/runtime compatibility. [S34] |
| 2 | Gradle lock and verification maintenance | Lockfiles and verification metadata with dependency updates | Define allowed output paths and run frozen/verification-enabled builds. Current Gradle support requires administrator permission to execute the wrapper for these operations. Generated checksums alone are not provenance approval. [S27] |
| 2 | Fleet drift and exception report | Read-only comparison of discovered versions against approved baselines | Custom coordinator report: current/target, owner, exception expiry, incompatible/unknown state. Missing extraction must appear as unknown, not compliant. No ticket for a held or unclassified item. |
| 3 | Toolchain consistency | Version references for runtimes and developer tools | Use native managers where present; custom extraction for remaining declared versions. Test all representations used by local development, CI, and containers. Avoid assuming all tools share one version scheme. [S34,S35] |
| 3 | Migration-assisted updates | Source/config changes from a pinned migration tool | Permit a narrowly defined post-upgrade task or dedicated executor. Nx/OpenRewrite are candidates needing recipe-specific evaluation; this research did not validate either integration. [S35,S36] |
| 3 | Versioned operational assets | Dashboard revisions, Helm charts, Terraform modules, internal baseline manifests | Native managers where supported; custom datasource only when needed. Require rendering/plan checks and ownership review, independent of application tests. [S29,S34] |

## How to align the JVM repositories

These mechanisms solve different problems:

- **Version catalog:** central aliases and requested dependency/plugin versions, optionally published for consumers. A catalog alone does not enforce the final resolved dependency graph. [S31]
- **Platform/BOM:** dependency constraints for a coordinated library set. Constraint semantics and conflicts still matter; verify resolved versions rather than assuming a platform import forces every requested version. [S30]
- **Published convention plugin:** reusable build behavior such as compiler options, test configuration, and lint setup. [S32]

Proposed example: release `company-jvm-platform:1.4.0`, validate it against a representative service, then let Renovate propose that dependency change in consumers. Publish convention-plugin changes independently unless a tested compatibility relationship requires them together. These example coordinates/versions are illustrative.

Central Renovate configuration can share update policy. It does not itself create a common Gradle dependency platform or prove compatibility. Merely grouping Kotlin, Gradle, a framework, and JDK updates into one MR does not discover which combination works. Maintain explicit supported cohorts and use CI to test them.

For repos that cannot adopt shared artifacts yet, start with a read-only drift inventory and centrally managed version rules. This costs less initially but retains duplicated build definitions. Prefer ordinary Maven/tagged releases over a bespoke version service; consider a custom datasource only for a baseline that cannot be represented through existing sources.

## Preserve the ticket-first flow

Recommended plan fields: schema version, repository and base SHA, workflow category, manager, exact current/target releases or digests, policy revision, campaign/cohort, allowed changed paths, validation profile, and stable change identity.

1. Planning establishes eligibility, compatibility cohort, capacity, and prerequisite results before ticket reservation.
2. Jira reserves/reuses the story for the stable repository/change identity. A campaign may have a parent ticket and individual service stories if workplace policy permits.
3. Execution checks that the plan is still valid, applies its exact target, and includes the story key from the first commit. A fresh registry lookup must not silently substitute another release.
4. Validation records actual changed files, MR/commit SHA, tests, approvals, and the final squash/merge commit. Plan changes invalidate old evidence.
5. The coordinator admits the next cohort after its defined acceptance gate. Renovate grouping is repository-scoped; cross-repository dependencies and release sequencing need explicit orchestration.

Keep campaign identity separate from run identity. Retry the same change without another Jira story; define explicitly whether a superseding target reuses an existing story or constitutes new work. Fleet concurrency limits belong in the coordinator. For commands that execute repository code, separate the build environment from the Jira reservation credentials.

## First three experiments

All proposed; no results claimed.

### A. Three-service JVM baseline

Create three synthetic Gradle Kotlin DSL services consuming one published test platform. Include one service with an intentionally incompatible constraint. Release a new platform and run existing discovery/Jira/execution.

Pass: supported consumers have one story and one MR each, all commits contain the key, resolved versions match expected constraints, reruns add no tickets, and the incompatible consumer is explicitly blocked or fails its gate without promotion. Lock/verification output is either correctly maintained or explicitly unsupported, never silently omitted. Do not require identical versions across intentionally distinct cohorts.

### B. GitLab template change

Use two consumers of a tagged test CI template. Publish a change that adds a harmless verification job; separately test a faulty template that removes a required job.

Pass: include refs update through ticketed MRs, the new job executes, and required-job validation rejects the faulty version even if the remaining jobs are green. A rerun reuses the story and MR.

### C. Canary failure, stale plan, and retry

Run one canary before two later consumers. Inject a canary failure, then test a passing revision. Move a target base branch between discovery and execution and retry reservation/execution after simulated interruption.

Pass: later consumers have no newly reserved tickets or MRs while held; stale plans are rejected/replanned; approved promotion opens only the permitted batch; interrupted work reconciles without duplicate stories; evidence is bound to the final SHA. If “canary success” includes deployment health, test that explicitly—CI alone proves only its checks.

## Shared agent skills via APM — added 2026-11-06

User-proposed workflow: a meaningful push or release to a shared skills repository should initiate updates in repositories consuming it through **APM (Agent Package Manager)**. Retain this alongside all the application, JVM, CI, infrastructure, and migration ideas above.

### Verified capabilities

Current Renovate documentation describes a native `apm` manager for `apm.yml`/`apm.yaml`, dependencies under `dependencies.apm` and `devDependencies.apm`, and `apm.lock.yaml` maintenance. Entries without an explicit ref are skipped. Supported tracking includes version tags and branch commits; SHA pins with a tag comment can retain release tracking. This is current-documentation evidence, not a test of our pinned lab image or the workplace worker. [S37]

APM documents lock generation without deploying files to agent targets, and frozen installation for replaying locked dependencies. This offers a useful separation between preparing the consumer change and checking that it installs reproducibly. [S38]

### Proposed flow

1. **Producer signal:** prefer an approved, immutable tagged skills release with release notes. Producer CI can trigger the automation pipeline immediately; scheduled discovery remains a reconciliation fallback. A meaningful push can also trigger discovery, but define its eligibility explicitly, such as approved changes to exported skills or their supporting scripts. Renovate cannot infer semantic importance from a push.
2. **Discover consumers:** scan enrolled repositories for declared dependencies on that package, honoring selected subpaths, supported release lines, exclusions, and rollout cohorts. Initially include direct consumers; explicitly report transitive-consumer coverage as unverified until tested.
3. **Plan:** capture package identity, previous and target release/commit, consumer base SHA, APM version, expected manifest/lock/generated-file changes, and the release campaign identifier. A push-triggered plan must retain the exact approved commit even if the branch moves later.
4. **Reserve Jira:** create or reuse the consumer story only once that consumer is eligible. Optionally link consumer stories to one campaign parent under the workplace policy.
5. **Execute:** update the declared skills reference and reconcile the lockfile to the planned target. Prefer native Renovate support after testing it. Use a narrowly scoped APM task only if the native path cannot maintain the required outputs. Avoid a broad dependency refresh that changes unrelated packages.
6. **Validate and review:** frozen install in an isolated checkout; check expected skills, relative links, helper scripts, generated output and selected agent targets. Preserve repository-owned instructions. Add a small representative skill-behavior evaluation where useful; successful installation alone does not prove useful agent behavior. Require owner review for changes to instructions, hooks, commands, or tool permissions.
7. **Promote:** merge the canary through existing controls, then admit later consumers. Retain the Jira key in the MR title and every commit, including squash/merge results.

Ownership: producer CI/GitLab starts runs; Renovate discovers and proposes dependency changes and applies update schedules; APM resolves/materializes skills; the existing coordinator manages tickets, retries, exact plans, and fleet promotion. Release notification is an additional trigger, not a replacement for reconciliation.

### Experiment D: shared skills release across three consumers

Use a synthetic APM skills package, two eligible consumers, and one intentionally excluded consumer. Release a visible skill change and run the workflow twice.

Pass criteria:

- Both eligible consumers receive exactly one ticketed MR; the excluded consumer receives no story or MR.
- Manifest and lockfile resolve to the planned commit; isolated frozen installs reproduce the expected skills.
- Local instructions and unrelated dependency pins remain unchanged; generated-file ownership is explicit.
- The second run creates no duplicate stories or MRs, including when a release event and scheduled run overlap.
- A documentation-only push outside the release policy creates no work. An approved release triggers discovery even if no application dependencies change.
- A broken package or failing canary prevents later-cohort ticket creation. A newer producer commit arriving during execution does not silently change the plan.

First implementation gate: confirm the exact Renovate/APM versions, private GitLab authentication, dependency syntax, and whether consumers commit generated skill files or install them from the lockfile. Prefer a tagged release pilot before testing moving-branch delivery. This is a documented proposal; no rollout was run.

## Alternatives, confidence, and next gate

Continue ordinary dependency updates only: lowest implementation cost, leaves organizational drift unresolved. Shared policies plus reporting: good first step if standards are not agreed. Shared versioned artifacts plus Renovate: preferred for repetitive established standards, but adds ownership/release obligations. Dedicated migration executor: appropriate for large source changes or unversioned template adoption; greater isolation and validation cost.

High confidence in native Gradle, GitLab include, custom-manager, and post-upgrade capabilities. Moderate confidence in their fit until one representative workplace Gradle build is inspected. Unknown: private Maven layout/auth, existing BOM/catalog/convention plugins, actual JDK/Kotlin/framework matrix, lock/verification use, and current coordinator plan semantics. Current docs may exceed the pinned local Renovate version; validate exact worker image before implementation.

Next decision: choose one existing shared JVM artifact, or a tagged CI template if JVM standards are still being defined, for a three-repository pilot. The workflow extensions in this document are proposed; the executable starter remains scoped as described in the README.

Sources S25–S38 are indexed in [workflow-sources.md](workflow-sources.md); all accessed 2026-11-06.
