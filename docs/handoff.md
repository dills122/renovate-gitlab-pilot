# First workplace handoff

**Request for the platform team.** We want a private GitLab automation project and two protected runner tags for a one-repo Renovate pilot. Can the runner pull our approved worker image and reach self-managed GitLab, the Azure npm feed, and our Jira API using approved machine identities? The first pipeline is discovery only. We will demonstrate a cold private dependency install and one patch candidate before requesting the first write.

| Owner | Supply or decide |
| --- | --- |
| Platform | Automation and sandbox project paths, GitLab API base and tier, runner host/network, image registry/repository and pull auth, architecture and internal CAs, secret store, persistent writer volume/backup, who can start or stop jobs. |
| App team | One real private dependency, base branch, pnpm/Node versions, dependency manifests and complete Angular/Nx patch group membership, required MR jobs and branch protection. |
| Feed team | Approved Azure feed URL, network policy and separate scoped read credentials for discovery, writer, and application CI. Confirm feed/upstream permissions when testing an uncached public package. |
| Jira owner | Jira edition, API endpoint/cloud ID, allowed machine authentication, test project, Story type, required fields, link permissions and test-account owner. |
| Change owner | Required independent human approvers, what happens on a new head, expected squash/merge subjects, retention and evidence location. |
| Operations | Who owns runner secrets, certificate and image rotation, expired tokens, pending Story reconciliation and pause/resume. |

**Import.** Create a private work automation repo using your normal bootstrap process. From an approved unpacked copy, copy this directory's contents (including hidden files) into that checkout. Rename `pilot.example.json` to `pilot.json` or copy it and fill in values. Submit the files through the normal protected-branch review. Use links to the work repo from internal Confluence or wiki pages; keep policy and commands in Git so reviewers can see changes.

**Local evidence from 2026-11-04.** The original fixture on GitLab EE 18.11.14 created KAN-7 before Renovate’s first commit, reused it on retry, maintained one backlink, and carried the key through squash and merge. The portable pipeline separately passed GitLab CI lint; its worker image built and ran its offline tests. Its report parser read the saved real Angular/Nx lookup and its Jira Cloud adapter verified the disposable Story and backlink. These are different checks. Run the workplace acceptance sequence on the approved environment to establish private Azure access, live writes from this port, Jira edition/fields, mandatory human approval and landed history.

**First decision.** Once discovery, a cold frozen install and actual application tests pass, show the artifact to the app and change owners. Then enable one ticket-first write and human-reviewed merge in the sandbox. Expand the repo allowlist only after recording the evidence.
