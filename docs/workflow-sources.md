# Workflow research sources

Accessed 2026-11-06. Source identifiers match [the workflow plan](polyrepo-workflows.md).


- S25. [Aircall: Keeping GitLab EKS Runner Up-to-Date with Renovate](https://aircall.io/blog/tech-team-stories/gitlab-eks-runner-renovate/). First-party deployment account; publication date not confirmed. Custom chart-version extraction and staged SRE/wider-runner updates.
- S26. [Nicolas Fränkel: Solving Gradle metadata and Renovate integration](https://blog.frankel.ch/gradle-metadata-renovate-integration/). First-person implementation account; publication date not confirmed. Post-upgrade metadata generation and its trust limitations.
- S27. [Renovate Gradle manager](https://docs.renovatebot.com/modules/manager/gradle/). Living documentation: extraction, lockfiles, verification, wrapper-execution permission.
- S28. [Jon Simeon: Configuring custom dependency managers in Renovate](https://jonsimeon.com/posts/by-slug/configuring-custom-dependency-managers-in-renovate/). Published 2026-09-22. First-person BlueBuild custom-manager example. Search-index text was available; direct page fetch failed during this pass.
- S29. [Renovate custom datasource](https://docs.renovatebot.com/modules/datasource/custom/). Living documentation: Grafana dashboard revisions and HTTP-served custom version inventories.
- S30. [Gradle platforms](https://docs.gradle.org/current/userguide/platforms.html). Living documentation: platform/BOM dependency constraints.
- S31. [Gradle version catalogs](https://docs.gradle.org/current/userguide/version_catalogs.html). Living documentation: catalog publishing/consumption and distinction from enforced resolution.
- S32. [Gradle plugin publishing](https://docs.gradle.org/current/userguide/publishing_gradle_plugins.html) and [shared build logic](https://docs.gradle.org/current/userguide/sharing_build_logic_between_subprojects.html). Living documentation: reusable build behavior and distribution mechanisms.
- S33. [Renovate GitLab CI include manager](https://docs.renovatebot.com/modules/manager/gitlabci-include/). Living documentation: project includes and GitLab tag datasource.
- S34. [Renovate managers](https://docs.renovatebot.com/modules/manager/). Living support inventory across application, infrastructure, and tooling files.
- S35. [Renovate custom managers and post-upgrade tasks](https://docs.renovatebot.com/configuration-options/). Living documentation: regex/JSONata extraction, command allowlisting and generated-file filtering.
- S36. [OpenRewrite documentation](https://docs.openrewrite.org/). Living documentation for source transformations. Candidate executor only; no Renovate/OpenRewrite integration tested in this research.

- S37. [Renovate APM manager](https://docs.renovatebot.com/modules/manager/apm/). Living documentation accessed 2026-11-06: Agent Package Manager manifests, ref tracking, and lockfile maintenance. Worker-version compatibility remains untested.
- S38. [APM lock](https://microsoft.github.io/apm/reference/cli/lock/), [dependency management](https://microsoft.github.io/apm/guides/dependencies/), and [APM update](https://microsoft.github.io/apm/reference/cli/update/). Official Agent Package Manager documentation accessed 2026-11-06: lockfile generation, frozen install, and dependency refresh semantics.
