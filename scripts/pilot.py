"""Protected GitLab pilot jobs: discover, ticket-first write, and read-only review."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

from policy import candidates, group_rule, lookup_policy, patch
from reservation import reserve
from services import GitLab, Jira, https


def config():
    c = json.loads(Path("pilot.json").read_text())
    https(c["feed"])
    if "YOUR-" in c["feed"] or c["repository"].startswith("your-group/"):
        raise ValueError("Replace example repository and feed settings in pilot.json")
    if not re.fullmatch(r"(?:@[a-z0-9._-]+/)?[a-z0-9][a-z0-9._-]*",c["privateProbe"]):
        raise ValueError("Specify the name of a private npm metadata probe")

    if not c["feed"].endswith("/npm/registry/") or not re.fullmatch(r"[A-Z][A-Z0-9]*", c["jira"]["project"]):
        raise ValueError("Check Azure feed URL and Jira project key")
    if not re.fullmatch(r"[a-z0-9-]+/", c["branchPrefix"]) or not c["requiredJobs"]:
        raise ValueError("Configure an isolated branch prefix and required jobs")
    if not c["groups"] or any(not re.fullmatch(r"[a-z0-9-]+", name) or len(set(g["packages"]))<2
                              for name,g in c["groups"].items()):
        raise ValueError("Provide named groups of two or more package pins")
    if c["repository"] == os.environ.get("CI_PROJECT_PATH"):
        raise ValueError("Use a separate target sandbox project")
    return c


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def artifact(file, data):
    Path(file).write_text(json.dumps(data, indent=2)+"\n")
    print(json.dumps(data), flush=True)


def context(c, gl):
    return {"pipeline":os.environ["CI_PIPELINE_ID"], "automation":os.environ["CI_PROJECT_ID"],
            "repository":c["repository"], "project":gl.get("")["id"], "base":c["base"],
            "sha":gl.head(), "policy":digest(c)}


def branch(c, choice):
    family, target = choice
    return c["branchPrefix"] + f"{family}-{target.replace('.', '-')}"


def owned(c, mr, project):
    return (mr["source_project_id"]==project==mr["target_project_id"] and mr["target_branch"]==c["base"]
            and mr["author"]["id"]==int(os.environ["BOT_USER_ID"]))


def select(c, gl, project, found):
    # One fixed selection is carried in the artifact, including across job retries.
    open_mrs = gl.pages("/merge_requests?state=opened")
    reuse = []
    for family, target in found:
        candidate = [family,target]
        matches = [mr for mr in open_mrs if mr["source_branch"]==branch(c,candidate)]
        if matches:
            if len(matches)!=1 or not owned(c,matches[0],project):
                raise ValueError("Unexpected MR owns the reserved branch name")
            reuse.append(candidate)
        else:
            g = c["groups"][family]
            # Another open MR may already contain the complete group at this target.
            covered = False
            for mr in open_mrs:
                if mr["source_project_id"] != project or mr["target_branch"] != c["base"]:
                    continue
                manifest = gl.manifest(g["manifest"], mr["sha"])
                if all(manifest.get(g["section"],{}).get(pkg)==target for pkg in g["packages"]):
                    covered = True
                    break
            if not covered:
                return candidate
    return reuse[0] if reuse else None


def child_env():
    return {k:os.environ[k] for k in ("HOME","PATH","SSL_CERT_FILE","NODE_EXTRA_CA_CERTS",
                                       "HTTPS_PROXY","HTTP_PROXY","NO_PROXY") if k in os.environ}


def feed_probe(c, directory):
    feed = c["feed"]
    password = os.environ["AZURE_FEED_TOKEN"]
    encoded = base64.b64encode(password.encode()).decode()
    url = urlsplit(feed)
    prefix = "//"+url.netloc+url.path
    lines = ["registry="+feed]
    for scope in (prefix, prefix.removesuffix("registry/")):
        lines.extend([scope+":username=pilot", scope+":_password="+encoded, scope+":email=pilot@example.invalid"])
    npmrc = Path(directory)/".npmrc"
    npmrc.write_text("\n".join(lines)+"\n")
    npmrc.chmod(0o600)
    try:
        version = subprocess.check_output(["pnpm","view",c["privateProbe"],"version","--registry",feed],
                                          cwd=directory,env=child_env(),text=True).strip()
        if not version:
            raise RuntimeError("Azure returned no version for the private probe")
        print(f"Private feed resolved {c['privateProbe']}",flush=True)
    finally:
        npmrc.unlink()


def renovate(c, policy, lookup):
    with tempfile.TemporaryDirectory() as tmp:
        feed_probe(c,tmp)
        report = Path(tmp)/"report.json"
        feed = c["feed"]
        # Force both lookup and lockfile operations to use the approved npm endpoint.
        policy = {**policy,"baseBranchPatterns":[c["base"]],"enabledManagers":["npm"],
                  "automerge":False,"platformAutomerge":False,"onboarding":False,
                  "pruneStaleBranches":False,"dependencyDashboard":False,
                  "npmrc":"registry="+feed+"\n","npmrcMerge":False}
        policy["packageRules"] = [*policy["packageRules"], {"matchManagers":["npm"],"registryUrls":[feed]}]
        auth = {"hostType":"npm","matchHost":feed.removesuffix("registry/"),"username":"pilot",
                "password":os.environ["AZURE_FEED_TOKEN"]}
        env = child_env() | {"RENOVATE_PLATFORM":"gitlab","RENOVATE_TOKEN":os.environ["GITLAB_TOKEN"],
              "RENOVATE_ENDPOINT":https(os.environ["CI_API_V4_URL"])+"/",
              "RENOVATE_REPOSITORIES":json.dumps([c["repository"]]),"RENOVATE_BASE_DIR":tmp,
              "RENOVATE_HOST_RULES":json.dumps([auth]),"RENOVATE_BINARY_SOURCE":"global",
              "RENOVATE_FORCE":json.dumps(policy),"RENOVATE_REQUIRE_CONFIG":"optional"}
        if lookup:
            env.update(RENOVATE_DRY_RUN="lookup", RENOVATE_REPORT_TYPE="file", RENOVATE_REPORT_PATH=str(report))
        subprocess.run(["renovate"],env=env,check=True)
        if lookup:
            return candidates(json.loads(report.read_text()),c["repository"],c["groups"])


def discover(c, gl):
    ctx = context(c,gl)
    found = renovate(c,lookup_policy(c["branchPrefix"],c["groups"]),True)
    choice = select(c,gl,ctx["project"],found)
    if gl.head()!=ctx["sha"]:
        raise ValueError("Target moved during discovery")
    artifact("patch-candidates.json", {"context":ctx,"candidates":found,"selected":choice})


def correlation(ctx, c, choice):
    identity = [https(os.environ["CI_API_V4_URL"]),ctx["project"],ctx["base"],choice,c["groups"][choice[0]],
                c["jira"]["apiBase"],c["jira"]["project"]]
    return "renovate-"+digest(identity)[:32]


def check_mr(c, gl, mr, project, choice, key):
    if (not owned(c,mr,project) or mr["source_branch"]!=branch(c,choice) or mr["state"]!="opened"
            or not mr["title"].startswith(key+" ")):
        raise ValueError("MR ownership, branch or title mismatch")
    commits = gl.pages(f"/merge_requests/{mr['iid']}/commits")
    if not commits or not all(x["message"].startswith(key+" ") for x in commits):
        raise ValueError("At least one commit lacks the expected ticket prefix")
    return [x["id"] for x in commits]


def write(c,gl):
    if os.environ.get("PILOT_WRITE_ENABLED")!="true":
        raise ValueError("Writer disabled; complete read-only acceptance first")
    plan = json.loads(Path("patch-candidates.json").read_text())
    ctx = context(c,gl)
    if plan["context"]!=ctx:
        raise ValueError("Discovery is stale or from another pipeline, target or policy")
    choice = plan["selected"]
    if choice is None:
        artifact("ticket-first-result.json", {"context":ctx,"status":"no eligible patch"})
        return
    if choice not in plan["candidates"]:
        raise ValueError("Selection absent from discovery")
    family,target = choice
    g = c["groups"][family]
    manifest = gl.manifest(g["manifest"],ctx["sha"])
    if not all(patch(manifest[g["section"]][p],target) for p in g["packages"]):
        raise ValueError("Group is no longer an aligned patch")
    if gl.api("GET","/user")["id"] != int(os.environ["BOT_USER_ID"]):
        raise ValueError("Unexpected GitLab writer identity")
    existing = [m for m in gl.pages("/merge_requests?state=opened") if m["source_branch"]==branch(c,choice)]
    if any(not owned(c,m,ctx["project"]) for m in existing):
        raise ValueError("Reserved branch belongs to another author/project")
    jira = Jira(c["jira"])
    label = correlation(ctx,c,choice)
    key = reserve(os.environ["PILOT_STATE"],label,f"Update {family} packages to {target}",jira)
    if gl.head()!=ctx["sha"]:
        raise ValueError("Target moved during Jira reservation; rediscover")
    rule = group_rule(family,c["groups"])
    rule.update(groupSlug=branch(c,choice).removeprefix(c["branchPrefix"]),allowedVersions="="+target,
                commitMessagePrefix=key,commitMessageLowerCase="never",prBodyNotes=["Tracking Story: "+key])
    renovate(c,{"branchPrefix":c["branchPrefix"],"separateMinorPatch":False,"packageRules":[{"matchPackageNames":["*"],"enabled":False},rule]},False)
    mr, = [m for m in gl.pages("/merge_requests?state=opened") if m["source_branch"]==branch(c,choice)
           and m["target_branch"]==ctx["base"]]
    commits = check_mr(c,gl,mr,ctx["project"],choice,key)
    jira.backlink(key,mr,write=True)
    artifact("ticket-first-result.json", {"context":ctx,"choice":choice,"story":key,"label":label,
             "iid":mr["iid"],"url":mr["web_url"],"sha":mr["sha"],"commits":commits})


def review(c,gl):
    r = json.loads(Path("ticket-first-result.json").read_text())
    ctx = context(c,gl)
    if r["context"]!=ctx:
        raise ValueError("Target or policy moved; rerun discovery and writer")
    if r.get("status")=="no eligible patch":
        artifact("review-result.json", {"decision":"no eligible patch"})
        return
    path = f"/merge_requests/{r['iid']}"
    mr = gl.get(path)
    if mr["sha"]!=r["sha"]:
        raise ValueError("New head requires a fresh writer result")
    commits = check_mr(c,gl,mr,ctx["project"],r["choice"],r["story"])
    family,target = r["choice"]
    g = c["groups"][family]
    diffs = gl.pages(path+"/diffs")
    if ({d["new_path"] for d in diffs}!={g["manifest"],c["lockfile"]} or
            any(d["old_path"]!=d["new_path"] or d.get("new_file") or d.get("deleted_file") for d in diffs)):
        raise ValueError("Unexpected files or renames")
    expected = copy.deepcopy(gl.manifest(g["manifest"],ctx["sha"]))
    for pkg in g["packages"]:
        if not patch(expected[g["section"]][pkg],target):
            raise ValueError("Not an eligible patch")
        expected[g["section"]][pkg] = target
    if expected!=gl.manifest(g["manifest"],mr["sha"]):
        raise ValueError("Unexpected manifest changes")
    pipe = mr.get("head_pipeline") or {}
    if pipe.get("status")!="success" or pipe.get("sha")!=mr["sha"] or pipe.get("source")!="merge_request_event":
        raise ValueError("Wait for a passing MR pipeline on this head")
    jobs = gl.pages(f"/pipelines/{pipe['id']}/jobs")
    for name in c["requiredJobs"]:
        if not any(j["name"]==name and j["status"]=="success" and not j["allow_failure"] for j in jobs):
            raise ValueError("Missing successful required job: "+name)
    jira = Jira(c["jira"])
    jira.verify(r["story"],correlation(ctx,c,r["choice"]))
    jira.backlink(r["story"],mr)
    final = gl.get(path)
    if final["sha"]!=mr["sha"] or final["title"]!=mr["title"] or final["state"]!="opened":
        raise ValueError("MR changed during review")
    artifact("review-result.json", {"decision":"eligible for human review","story":r["story"],"mr":mr["web_url"],
             "sha":mr["sha"],"pipeline":pipe["id"],"commits":commits})


if __name__=="__main__":
    mode, = sys.argv[1:]
    try:
        cfg = config()
        {"discover":discover,"write":write,"review":review}[mode](cfg,GitLab(cfg))
    except Exception as exc:
        if mode=="review":
            artifact("review-result.json", {"decision":"hold","reason":str(exc)})
        raise
