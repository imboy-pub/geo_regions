#!/usr/bin/env python3
"""Import this delivery into its existing git repository without overwriting files.

Defaults to a read-only plan. --apply creates only missing files. Conflicts abort
before any write; resolve them explicitly and rerun. No git commit/push/delete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SKIP = {'.git', '.dart_tool', '__pycache__', '.venv', 'node_modules', 'build', 'generated'}
SKIP_FILES = {'.plans/geo-regions-v1/state.json', '.plans/geo-regions-v1/state.lock'}
REMOTES = {'https://github.com/imboy-pub/geo_regions',
           'https://github.com/imboy-pub/geo_regions.git',
           'git@github.com:imboy-pub/geo_regions.git',
           'ssh://git@github.com/imboy-pub/geo_regions.git'}


def git(target, *args):
    return subprocess.check_output(['git', '-C', str(target), *args], text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_parents(target, destination):
    current = destination
    while current != target:
        if current.is_symlink():
            raise ValueError(f'Refusing target symlink: {current}')
        if current != destination and current.exists() and not current.is_dir():
            raise ValueError(f'Non-directory parent: {current}')
        current = current.parent


def plan(source, target):
    if not target.is_dir():
        raise ValueError('Target must be an existing repository directory.')
    if Path(git(target, 'rev-parse', '--show-toplevel')).resolve() != target:
        raise ValueError('Target must be the git worktree root, not a subdirectory.')
    if git(target, 'remote', 'get-url', 'origin') not in REMOTES:
        raise ValueError('origin is not the expected imboy-pub/geo_regions repository.')
    if source == target or source.is_relative_to(target) or target.is_relative_to(source):
        raise ValueError('Keep the extracted delivery outside the target repository.')
    operations, identical, conflicts = [], [], []
    for src in sorted(source.rglob('*')):
        rel = src.relative_to(source)
        if any(part in SKIP for part in rel.parts) or rel.as_posix() in SKIP_FILES:
            continue
        if src.is_symlink():
            raise ValueError(f'Refusing source symlink: {rel}')
        if not src.is_file():
            continue
        dst = target / rel
        check_parents(target, dst)
        if dst.exists():
            if dst.is_file() and digest(src) == digest(dst):
                identical.append(rel.as_posix())
            else:
                conflicts.append(rel.as_posix())
        else:
            operations.append((src, dst, rel.as_posix()))
    return operations, identical, conflicts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    original_target = Path(os.path.abspath(args.target.expanduser()))
    try:
        for component in (original_target, *original_target.parents):
            if component.is_symlink():
                raise ValueError(f'Refusing symlink in target root: {component}')
        target = original_target.resolve()
        operations, identical, conflicts = plan(source, target)
        result = {'mode': 'apply' if args.apply else 'dry-run', 'target': str(target),
                  'create': [op[2] for op in operations], 'identical': identical,
                  'conflicts': conflicts, 'overwrites': 0}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if conflicts:
            print('Conflicts found. No files were written; merge differences deliberately.', file=sys.stderr)
            return 2
        if args.apply:
            for src, dst, _ in operations:
                check_parents(target, dst)
                dst.parent.mkdir(parents=True, exist_ok=True)
                with src.open('rb') as incoming, dst.open('xb') as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
                os.chmod(dst, src.stat().st_mode & 0o777)
            print(f'Created {len(operations)} new files; preserved {len(identical)} identical files.')
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'Import stopped: {exc}. Existing files were not overwritten.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
