#!/usr/bin/env python3
"""Persist ZCODE task status and evidence; never execute or certify the plan.

Use status --json to mirror tasks into a real task panel. Completion records
artifact hashes and a successful command string; the coordinator must inspect
the actual command output. This helper is not a test runner or proof of review.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / '.plans/geo-regions-v1'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_atomic(path, value):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as f:
        name = f.name
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
    try:
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_owned_path(path):
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError('State/evidence path escaped the repository.')
    current = path
    while current != ROOT:
        if current.is_symlink():
            raise ValueError(f'State/evidence path must not contain symlinks: {current}')
        current = current.parent


def git(*args):
    result = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


@contextmanager
def lock():
    path = PLAN / 'state.lock'
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError('State writer lock exists. Inspect its owner; do not blindly delete it.') from exc
    try:
        os.write(fd, json.dumps({'pid': os.getpid(), 'at': now()}).encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def evidence_path(raw):
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT) or not path.is_file() or path.is_symlink():
        raise ValueError('Evidence must be an existing, non-symlink file inside the repository.')
    safe_owned_path(path)
    if not path.stat().st_size:
        raise ValueError('Empty evidence cannot complete a task.')
    return resolved.relative_to(ROOT).as_posix(), sha(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('init')
    status = sub.add_parser('status')
    status.add_argument('--json', action='store_true')
    sub.add_parser('verify-evidence')
    for name in ('start', 'block', 'complete', 'reopen'):
        item = sub.add_parser(name)
        item.add_argument('task')
        item.add_argument('--note', default='')
        if name == 'complete':
            item.add_argument('--evidence', action='append', required=True)
            item.add_argument('--command', required=True)
    args = parser.parse_args()
    path = PLAN / 'state.json'
    for item in (PLAN, PLAN / 'tasks.json', path, PLAN / 'state.lock'):
        safe_owned_path(item)
    spec = read(PLAN / 'tasks.json')
    task_defs = {item['id']: item for item in spec['tasks']}
    if args.action == 'init':
        with lock():
            if not path.exists():
                state = {'taskId': spec['taskId'], 'planSha256': sha(PLAN / 'tasks.json'),
                         'createdAt': now(), 'worktree': str(ROOT), 'branch': git('branch', '--show-current'),
                         'baseCommit': git('rev-parse', 'HEAD'), 'tasks': {
                             key: {'status': 'pending', 'evidence': [], 'history': []} for key in task_defs}}
                write_atomic(path, state)
        print('State ready; existing state was preserved.')
        return 0
    if not path.exists():
        raise ValueError('Run plan_status.py init first.')
    state = read(path)
    if args.action in ('status', 'verify-evidence'):
        if args.action == 'status':
            if args.json:
                print(json.dumps({'definition': spec, 'state': state}, ensure_ascii=False, indent=2))
            else:
                for task in spec['tasks']:
                    row = state['tasks'].get(task['id'], {'status': 'missing'})
                    print(f"{task['id']:7} {row['status']:12} {task['titleZh']}")
                if state.get('planSha256') != sha(PLAN / 'tasks.json'):
                    print('PLAN_CHANGED: reconcile tasks and revalidate affected evidence.')
            return 0
        errors = []
        for key, row in state['tasks'].items():
            if row['status'] != 'completed':
                continue
            if not row.get('evidence'):
                errors.append(key + ': no evidence')
            for item in row.get('evidence', []):
                try:
                    _, actual = evidence_path(item['path'])
                    if actual != item['sha256']:
                        errors.append(key + ': changed evidence ' + item['path'])
                except (OSError, ValueError) as exc:
                    errors.append(key + ': invalid evidence ' + str(exc))
        print(json.dumps({'errors': errors, 'note': 'Hashes only; input/code changes still require coordinator review.'}, indent=2))
        return 2 if errors else 0
    if args.task not in task_defs:
        raise ValueError('Unknown task ID.')
    with lock():
        state = read(path)
        if state.get('planSha256') != sha(PLAN / 'tasks.json'):
            raise ValueError('Task definition changed. Reconcile state explicitly; do not silently reset it.')
        row = state['tasks'][args.task]
        if args.action in ('start', 'complete'):
            unmet = [key for key in task_defs[args.task]['dependsOn'] if state['tasks'][key]['status'] != 'completed']
            if unmet:
                raise ValueError('Unfinished dependencies: ' + ', '.join(unmet))
        if args.action == 'start':
            if row['status'] == 'completed':
                raise ValueError('Task is completed; use reopen with a reason after checking downstream impact.')
            row['status'] = 'in_progress'
        elif args.action == 'block':
            if row['status'] == 'completed':
                raise ValueError('Use reopen first to invalidate completed downstream tasks.')
            if not args.note:
                raise ValueError('A concrete blocking reason is required.')
            row['status'] = 'blocked'
        elif args.action == 'reopen':
            if not args.note:
                raise ValueError('A revalidation reason is required.')
            row['status'] = 'pending'
            # Invalidate transitive consumers so old completion does not mask changed prerequisites.
            invalidated = {args.task}
            changed = True
            while changed:
                changed = False
                for key, task in task_defs.items():
                    if key not in invalidated and invalidated.intersection(task['dependsOn']):
                        invalidated.add(key)
                        state['tasks'][key]['status'] = 'pending'
                        state['tasks'][key]['history'].append({'at': now(), 'action': 'dependency-invalidated', 'note': args.task})
                        changed = True
        elif args.action == 'complete':
            if row['status'] != 'in_progress':
                raise ValueError('Only an in-progress task can complete.')
            row['evidence'] = [{'path': rel, 'sha256': digest} for rel, digest in map(evidence_path, args.evidence)]
            row['lastVerifiedCommand'] = args.command
            row['verifiedCommit'] = git('rev-parse', 'HEAD')
            row['status'] = 'completed'
        row['history'].append({'at': now(), 'action': args.action, 'note': args.note})
        state['updatedAt'] = now()
        write_atomic(path, state)
    print(f'{args.task}: {row["status"]}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f'State error: {exc}', file=sys.stderr)
        raise SystemExit(2)
