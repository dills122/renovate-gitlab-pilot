"""Regression tests for operations that can produce duplicate tickets or unsafe writes."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch as replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import pilot
from policy import candidates
from reservation import reserve


class Reservation(unittest.TestCase):
    def test_lost_response_reconciles_before_new_create(self):
        jira = Mock()
        jira.search.side_effect = [None,None,"APP-1"]
        jira.create.side_effect = TimeoutError("response lost")
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(RuntimeError,"volume"):
                reserve(d,"label","summary",jira)
            Path(d,".pilot-state-volume").touch()
            with self.assertRaises(TimeoutError):
                reserve(d,"label","summary",jira)
            with self.assertRaisesRegex(RuntimeError,"Unconfirmed"):
                reserve(d,"label","summary",jira)
            self.assertEqual(reserve(d,"label","summary",jira),"APP-1")
            self.assertEqual(reserve(d,"label","summary",jira),"APP-1")
            jira.create.assert_called_once()


class Flow(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/"pilot.example.json").read_text())
        self.env = replace.dict(os.environ,{"CI_PIPELINE_ID":"10","CI_PROJECT_ID":"3","BOT_USER_ID":"20",
                    "CI_API_V4_URL":"https://gitlab.example/api/v4","PILOT_WRITE_ENABLED":"true"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.gl = Mock()
        self.gl.get.return_value = {"id":77}
        self.gl.head.return_value = "sha1"

    def test_minor_or_partial_group_never_selected(self):
        c = self.config
        deps = []
        for g in c["groups"].values():
            for p in g["packages"]:
                deps.append({"depName":p,"depType":g["section"],"currentValue":"2.0.1","updates":[
                    {"updateType":"patch","newValue":"2.0.2","branchName":"group"},
                    {"updateType":"minor","newValue":"2.1.0","branchName":"group"}]})
        deps[0]["updates"].pop(0)
        report = {"problems":[],"repositories":{c["repository"]:{"problems":[],
                  "packageFiles":{"npm":[{"packageFile":"package.json","deps":deps}]}}}}
        self.assertEqual(candidates(report,c["repository"],c["groups"]),[("nx","2.0.2")])

    def test_stale_artifact_stops_before_jira(self):
        plan = {"context":pilot.context(self.config,self.gl),"selected":["nx","2.0.2"]}
        self.gl.head.return_value = "sha2"
        with replace.object(Path,"read_text",return_value=json.dumps(plan)), replace.object(pilot,"Jira") as jira:
            with self.assertRaisesRegex(ValueError,"stale"):
                pilot.write(self.config,self.gl)
            jira.assert_not_called()

    def test_checks_each_commit_even_when_title_is_correct(self):
        mr = {"source_project_id":77,"target_project_id":77,"target_branch":"main","author":{"id":20},
              "source_branch":"renovate-pilot/nx-2-0-2","state":"opened","iid":1,"title":"APP-1 update"}
        self.gl.pages.return_value = [{"id":"ok","message":"APP-1 update"},{"id":"bad","message":"forgot key"}]
        with self.assertRaisesRegex(ValueError,"commit"):
            pilot.check_mr(self.config,self.gl,mr,77,["nx","2.0.2"],"APP-1")

    def test_cold_ci_hold_when_required_job_skipped(self):
        ctx = pilot.context(self.config,self.gl)
        r = {"context":ctx,"choice":["nx","2.0.2"],"story":"APP-1","iid":1,"sha":"source"}
        mr = {"sha":"source","head_pipeline":{"id":9,"status":"success","sha":"source","source":"merge_request_event"}}
        self.gl.get.side_effect=lambda path: {"id":77} if not path else mr
        self.gl.pages.side_effect = [[{"old_path":p,"new_path":p} for p in ("package.json","pnpm-lock.yaml")],
                                     [{"name":"verify-workspace","status":"skipped","allow_failure":False}]]
        self.gl.manifest.side_effect=[{"devDependencies":dict.fromkeys(("nx","@nx/angular"),v)} for v in ("2.0.1","2.0.2")]
        with replace.object(Path,"read_text",return_value=json.dumps(r)),replace.object(pilot,"check_mr"):
            with self.assertRaisesRegex(ValueError,"required job"):
                pilot.review(self.config,self.gl)


if __name__ == "__main__":
    unittest.main()
