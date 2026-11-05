"""HTTPS clients restricted to configured hosts. Never follow credentialed redirects."""
import base64
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def https(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Expected a plain HTTPS endpoint without embedded credentials")
    return url.rstrip("/")


def client(base, headers):
    base = https(base)
    def call(method, path, body=None):
        req = Request(base + path, method=method, headers={**headers, "Content-Type":"application/json"},
                      data=json.dumps(body).encode() if body is not None else None)
        try:
            with build_opener(NoRedirect()).open(req, timeout=30) as response:
                data = response.read()
                return json.loads(data) if data else None
        except HTTPError as exc:
            raise RuntimeError(f"{method} {path.split('?')[0]} returned HTTP {exc.code}") from None
    return call


class GitLab:
    def __init__(self, config):
        self.api = client(os.environ["CI_API_V4_URL"], {"PRIVATE-TOKEN":os.environ["GITLAB_TOKEN"]})
        self.path = "/projects/" + quote(config["repository"], safe="")
        self.base = config["base"]

    def get(self, path):
        return self.api("GET", self.path + path)

    def head(self):
        return self.get("/repository/branches/" + quote(self.base, safe=""))["commit"]["id"]

    def pages(self, path):
        rows = []
        for page in range(1,101):
            batch = self.get(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
            rows.extend(batch)
            if len(batch)<100:
                return rows
        raise ValueError("Exceeded pilot pagination limit")

    def manifest(self, path, ref):
        data = self.get("/repository/files/" + quote(path,safe="") + "?ref=" + quote(ref,safe=""))
        return json.loads(base64.b64decode(data["content"]))


class Jira:
    def __init__(self, config):
        self.config = config
        base = https(config["apiBase"])
        if config["kind"]=="cloud" and re.fullmatch(r"https://api\.atlassian\.com/ex/jira/[0-9a-fA-F-]{36}/rest/api/3",base):
            auth = base64.b64encode((os.environ["JIRA_EMAIL"]+":"+os.environ["JIRA_TOKEN"]).encode()).decode()
            headers = {"Authorization":"Basic "+auth}
        elif config["kind"]=="data-center" and base.endswith("/rest/api/2"):
            headers = {"Authorization":"Bearer "+os.environ["JIRA_TOKEN"]}
        else:
            raise ValueError("Check Jira edition and API base")
        self.call = client(base, headers)

    def search(self, label):
        path = "/search/jql" if self.config["kind"]=="cloud" else "/search"
        result = self.call("POST",path,{"jql":f'project = {self.config["project"]} AND labels = "{label}"',
                                        "fields":["issuetype"],"maxResults":2})
        rows = result["issues"]
        if len(rows)>1 or result.get("nextPageToken") or result.get("total",0)>1:
            raise ValueError("Multiple issues share the reservation label")
        return rows[0]["key"] if rows else None

    def create(self, label, summary):
        fields = {**self.config["extraFields"], "project":{"key":self.config["project"]},
                  "issuetype":{"name":self.config["issueType"]},"labels":[label],"summary":summary}
        return self.call("POST","/issue",{"fields":fields})["key"]

    def verify(self, key, label):
        if not re.fullmatch(re.escape(self.config["project"])+r"-[1-9]\d*",key):
            raise ValueError("Unexpected Jira key")
        fields = self.call("GET","/issue/"+key+"?fields=project,issuetype,labels")["fields"]
        if (fields["project"]["key"]!=self.config["project"] or fields["issuetype"]["name"]!=self.config["issueType"]
                or label not in fields["labels"]):
            raise ValueError("Jira issue no longer matches the reservation")

    def backlink(self, key, mr, write=False):
        path = "/issue/"+key+"/remotelink"
        if write:
            self.call("POST",path,{"globalId":mr["web_url"],"object":{"url":mr["web_url"],"title":mr["title"]}})
        links = self.call("GET",path)
        if sum(l["object"]["url"]==mr["web_url"] for l in links)!=1:
            raise ValueError("Expected exactly one MR backlink")
