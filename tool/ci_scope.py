#!/usr/bin/env python3
"""Choose the expensive Flutter gate; the workflow itself always reports a gate."""

import os
from pathlib import Path
import re
import subprocess


def main():
    event = os.environ.get("CI_EVENT", "")
    base = os.environ.get("CI_BASE", "")
    force = os.environ.get("CI_FORCE_FLUTTER", "").lower() == "true"
    if force or event not in ("push", "pull_request") or not re.fullmatch(r"[a-f0-9]{40}", base) or set(base) == {"0"}:
        changed, flutter = [], True
        reason = "full verification requested or no comparable base"
    else:
        result = subprocess.run(["git", "diff", "--name-only", base, "HEAD", "--"], capture_output=True, text=True)
        if result.returncode:
            changed, flutter = [], True
            reason = "base unavailable; conservative full verification"
        else:
            changed = result.stdout.splitlines()
            flutter = any(path.endswith(".dart") or path.startswith(("lib/", "test/", "example/", "demo/flutter/", "schemas/", ".github/workflows/")) or path in ("config/readiness.json", "config/data_policy.json", "tool/check_readiness.py", "tool/import_data.py") or Path(path).name in ("pubspec.yaml", "pubspec.lock", "analysis_options.yaml", ".flutter-version") for path in changed)
            reason = "Flutter/build/contract inputs changed" if flutter else "data content, unrelated tools, or documentation changes only"
    value = "true" if flutter else "false"
    print(f"flutter={value}; {reason}; changedFiles={len(changed)}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"flutter={value}\n")


if __name__ == "__main__":
    main()
