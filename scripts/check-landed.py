"""Read-only check in a target checkout: inspect every commit introduced by one MR."""
import argparse
import re
import subprocess


def git(*args):
    return subprocess.check_output(["git",*args],text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", help="target SHA immediately before the merge")
    parser.add_argument("after", help="target SHA immediately after the merge")
    parser.add_argument("story")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Z][A-Z0-9]*-[1-9]\d*",args.story):
        parser.error("Expected a Jira key")
    if not all(re.fullmatch(r"[0-9a-f]{7,64}",s) for s in (args.before,args.after)):
        parser.error("Pass exact Git commit SHAs")
    subprocess.run(["git","merge-base","--is-ancestor",args.before,args.after],check=True)
    commits = git("rev-list","--reverse",args.before+".."+args.after).splitlines()
    if not commits:
        raise SystemExit("No commits introduced")
    for sha in commits:
        subject = git("show","-s","--format=%s",sha)
        if not subject.startswith(args.story+" "):
            raise SystemExit(f"Missing {args.story} prefix on {sha}")
        print(sha[:12],subject)


if __name__=="__main__":
    main()
