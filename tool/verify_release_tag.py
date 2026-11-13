#!/usr/bin/env python3
"""Check remote lightweight/annotated tag still matches the tested commit.

Uses authenticated gh api in the release job. Tag rules remain necessary to
prevent a later administrator mutation after this point-in-time check.
"""

import argparse
import json
import os
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"data-v[0-9]{4}\.[0-9]{2}\.[0-9]{2}(?:\.[0-9]+)?", args.tag):
        parser.error("invalid data tag")
    if not re.fullmatch(r"[a-f0-9]{40}", args.commit):
        parser.error("commit must be a full SHA")
    repository = os.environ.get("GH_REPO", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        parser.error("GH_REPO must be owner/repository")

    def get(path):
        result = subprocess.run(["gh", "api", f"repos/{repository}/{path}"], check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    obj = get("git/ref/tags/" + args.tag)["object"]
    for _ in range(8):
        if obj["type"] == "commit":
            if obj["sha"] != args.commit:
                parser.error("remote tag changed after verification; refusing to release")
            print(f"remote tag matches tested commit {args.commit}")
            return
        if obj["type"] != "tag" or not re.fullmatch(r"[a-f0-9]{40}", obj["sha"]):
            parser.error("tag does not resolve to a commit")
        obj = get("git/tags/" + obj["sha"])["object"]
    parser.error("annotated tag nesting exceeds supported depth")


if __name__ == "__main__":
    main()
