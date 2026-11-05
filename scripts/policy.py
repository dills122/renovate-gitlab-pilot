"""Find package groups with the same stable patch target in a Renovate lookup report."""
import re

STABLE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")


def version_parts(value):
    match = STABLE.fullmatch(value or "")
    return tuple(map(int, match.groups())) if match else None


def patch(current, target):
    old, new = version_parts(current), version_parts(target)
    return old and new and old[:2] == new[:2] and new > old


def group_rule(family, groups):
    return {"enabled": True, "matchPackageNames": groups[family]["packages"], "matchFileNames": [groups[family]["manifest"]],
            "groupName": f"{family.title()} patches", "groupSlug": family,
            "allowedVersions": r"/^\d+\.\d+\.\d+$/"}


def candidates(report, target, groups):
    repo = report["repositories"][target]
    if report["problems"] or repo["problems"]:
        raise ValueError("Renovate reported discovery problems; no Story reserved")
    files = {f["packageFile"]: f for f in repo["packageFiles"]["npm"]}
    result = []
    for family, group in groups.items():
        manifest, section, packages = group["manifest"], group["section"], group["packages"]
        targets = []
        for name in packages:
            dep, = [d for d in files[manifest]["deps"] if d["depName"] == name and d["depType"] == section]
            if dep.get("warnings"):
                raise ValueError(f"Renovate lookup warnings for {name}")
            updates = {(u["branchName"], u["newValue"]) for u in dep.get("updates", [])
                       if u.get("updateType") == "patch" and patch(dep["currentValue"], u.get("newValue"))}
            targets.append(updates)
        aligned = set.intersection(*targets)
        if aligned:
            _, target = max(aligned, key=lambda pair: version_parts(pair[1]))
            result.append((family, target))
    return result


def lookup_policy(prefix, groups):
    return {"branchPrefix": prefix, "separateMinorPatch": True,
              "packageRules": [{"matchPackageNames": ["*"], "enabled": False},
                               *(group_rule(family, groups) for family in groups)]}
