"""Exercise the actual artifact handoff with fake external services, including a retry."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import pilot


class Handoff(unittest.TestCase):
    def test_one_story_from_lookup_through_review(self):
        cfg = json.loads((ROOT/"pilot.example.json").read_text())
        cfg["groups"] = {"nx":cfg["groups"]["nx"]}
        gl, jira = Mock(), Mock()
        gl.api.return_value = {"id":8}
        gl.head.return_value = "mainsha"
        mrs = []
        def get(path):
            return {"id":16} if path=="" else mrs[0]
        gl.get.side_effect = get
        def pages(path):
            if path.startswith("/merge_requests?"): return mrs
            if path.endswith("/commits"): return [{"id":"commit","message":"APP-3 update"}]
            if path.endswith("/diffs"): return [dict(old_path=p,new_path=p) for p in ("package.json","pnpm-lock.yaml")]
            if path.endswith("/jobs"): return [{"name":"verify-workspace","status":"success","allow_failure":False}]
            raise AssertionError(path)
        gl.pages.side_effect = pages
        gl.manifest.side_effect = lambda p,ref: {"devDependencies": dict.fromkeys(("nx","@nx/angular"),
                                                          "2.0.1" if ref=="mainsha" else "2.0.2")}
        jira.search.return_value = None
        jira.create.return_value = "APP-3"
        def run(config,policy,lookup):
            if lookup: return [("nx","2.0.2")]
            rule = policy["packageRules"][1]
            self.assertEqual(rule["commitMessagePrefix"],"APP-3")
            self.assertEqual(rule["allowedVersions"],"=2.0.2")
            if not mrs:
                mrs.append(dict(iid=1,source_branch="renovate-pilot/nx-2-0-2",target_branch="main",
                          title="APP-3 update",state="opened",web_url="https://example.invalid/mr/1",
                          author={"id":8},source_project_id=16,target_project_id=16,sha="commit",
                          head_pipeline={"id":7,"sha":"commit","status":"success","source":"merge_request_event"}))
        with TemporaryDirectory() as tmp, ExitStack() as stack:
            start=os.getcwd()
            os.chdir(tmp)
            stack.callback(os.chdir,start)
            Path(".pilot-state-volume").touch()
            stack.enter_context(patch.dict(os.environ,{"PILOT_STATE":tmp,"BOT_USER_ID":"8","CI_PIPELINE_ID":"3",
                "CI_PROJECT_ID":"7","PILOT_WRITE_ENABLED":"true","CI_API_V4_URL":"https://example.invalid/api/v4"}))
            stack.enter_context(patch.object(pilot,"renovate",side_effect=run))
            stack.enter_context(patch.object(pilot,"Jira",return_value=jira))
            pilot.discover(cfg,gl)
            pilot.write(cfg,gl)
            original=Path("ticket-first-result.json").read_text()
            pilot.write(cfg,gl)
            self.assertEqual(original,Path("ticket-first-result.json").read_text())
            jira.create.assert_called_once()
            pilot.review(cfg,gl)
            self.assertEqual(json.loads(Path("review-result.json").read_text())["decision"],"eligible for human review")
