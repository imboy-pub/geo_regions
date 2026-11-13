"""Safety regressions for delivery installation and persistent task helpers.

All mutations happen inside isolated temporary directories. Test Git repositories
have no commits and are never fetched or pushed. No user checkout or shared plan
state is touched. Run with:

    python3 -m unittest discover -s tests -p test_delivery_helpers.py -v
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ORIGIN = 'https://github.com/imboy-pub/geo_regions'


class DeliveryHelperSafetyTests(unittest.TestCase):
    """Seventeen independent safety-contract checks using public CLI entry points."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='geo-regions-helper-test-')
        self.addCleanup(self.temporary.cleanup)
        # Canonicalize the platform temp directory itself (e.g. macOS /var).
        # Deliberate test symlinks are created only below this real directory.
        self.temp = Path(self.temporary.name).resolve()

    def command(self, *arguments):
        return subprocess.run(
            [str(argument) for argument in arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)

    def failure(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)

    def installer_fixture(self):
        source = self.temp / 'source'
        target = self.temp / 'repository'
        (source / 'tool').mkdir(parents=True)
        target.mkdir()
        shutil.copy2(PACKAGE_ROOT / 'tool/install_bundle.py', source / 'tool/install_bundle.py')
        (source / 'existing.txt').write_text('same bytes\n', encoding='utf-8')
        (source / 'new.txt').write_text('new bytes\n', encoding='utf-8')
        excluded = source / '.plans/geo-regions-v1'
        excluded.mkdir(parents=True)
        (excluded / 'state.json').write_text('DO NOT IMPORT SOURCE STATE\n', encoding='utf-8')
        # No user Git config is edited and no remote command is executed.
        self.success(self.command('git', '-c', 'init.defaultBranch=main', 'init', '--quiet', '--template=', target))
        self.success(self.command('git', '-C', target, 'remote', 'add', 'origin', EXPECTED_ORIGIN))
        return source, target

    def install(self, source, target, mode='--apply'):
        return self.command(sys.executable, source / 'tool/install_bundle.py', '--target', target, mode)

    @staticmethod
    def snapshot(directory):
        """Compare existing file bytes and identity without reading Git internals."""
        return {
            path.relative_to(directory).as_posix(): (
                hashlib.sha256(path.read_bytes()).hexdigest(),
                path.stat().st_mtime_ns,
                path.stat().st_ino,
            )
            for path in directory.rglob('*')
            if path.is_file() and '.git' not in path.relative_to(directory).parts
        }

    def plan_fixture(self):
        project = self.temp / 'project'
        (project / 'tool').mkdir(parents=True)
        plan = project / '.plans/geo-regions-v1'
        plan.mkdir(parents=True)
        shutil.copy2(PACKAGE_ROOT / 'tool/plan_status.py', project / 'tool/plan_status.py')
        specification = {
            'taskId': 'helper-safety-fixture',
            'tasks': [
                {'id': 'A', 'titleZh': 'A', 'dependsOn': []},
                {'id': 'B', 'titleZh': 'B', 'dependsOn': ['A']},
                {'id': 'C', 'titleZh': 'C', 'dependsOn': ['B']},
            ],
        }
        (plan / 'tasks.json').write_text(json.dumps(specification), encoding='utf-8')
        return project, plan, specification

    def plan_command(self, project, *arguments):
        return self.command(sys.executable, project / 'tool/plan_status.py', *arguments)

    def initialized_plan(self):
        project, plan, specification = self.plan_fixture()
        self.success(self.plan_command(project, 'init'))
        return project, plan, specification

    @staticmethod
    def state(plan):
        return json.loads((plan / 'state.json').read_text(encoding='utf-8'))

    def complete_fixture_task(self, project, task):
        evidence = project / 'evidence.txt'
        evidence.write_text('PASS: isolated unit-test fixture\n', encoding='utf-8')
        self.success(self.plan_command(project, 'start', task))
        self.success(self.plan_command(
            project, 'complete', task,
            '--command', 'isolated unit-test fixture',
            '--evidence', 'evidence.txt',
        ))

    def test_installer_rejects_other_origin_without_writes(self):
        source, target = self.installer_fixture()
        self.success(self.command('git', '-C', target, 'remote', 'set-url', 'origin', 'https://github.com/example/other'))
        before = self.snapshot(target)
        self.failure(self.install(source, target))
        self.assertEqual(self.snapshot(target), before)

    def test_installer_conflict_aborts_entire_batch_before_writing(self):
        source, target = self.installer_fixture()
        (target / 'existing.txt').write_text('USER CONTENT\n', encoding='utf-8')
        before = self.snapshot(target)
        self.failure(self.install(source, target))
        self.assertEqual(self.snapshot(target), before)
        self.assertFalse((target / 'new.txt').exists())

    def test_installer_creates_missing_files_and_excludes_shared_state(self):
        source, target = self.installer_fixture()
        (target / 'existing.txt').write_text('same bytes\n', encoding='utf-8')
        self.success(self.install(source, target))
        self.assertEqual((target / 'new.txt').read_bytes(), (source / 'new.txt').read_bytes())
        self.assertFalse((target / '.plans/geo-regions-v1/state.json').exists())

    def test_installer_rerun_preserves_bytes_mtimes_and_inodes(self):
        source, target = self.installer_fixture()
        self.success(self.install(source, target))
        before = self.snapshot(target)
        self.success(self.install(source, target))
        self.assertEqual(self.snapshot(target), before)

    def test_installer_rejects_source_symlink(self):
        source, target = self.installer_fixture()
        (source / 'source-link').symlink_to(source / 'existing.txt')
        before = self.snapshot(target)
        self.failure(self.install(source, target))
        self.assertEqual(self.snapshot(target), before)

    def test_installer_rejects_destination_ancestor_symlink(self):
        source, target = self.installer_fixture()
        (source / 'nested').mkdir()
        (source / 'nested/file.txt').write_text('payload\n', encoding='utf-8')
        outside = self.temp / 'outside'
        outside.mkdir()
        (target / 'nested').symlink_to(outside, target_is_directory=True)
        self.failure(self.install(source, target))
        self.assertFalse((outside / 'file.txt').exists())

    def test_installer_rejects_symlink_target_repository_root(self):
        source, target = self.installer_fixture()
        alias = self.temp / 'repository-link'
        alias.symlink_to(target, target_is_directory=True)
        self.failure(self.install(source, alias, '--dry-run'))
        self.assertFalse((target / 'new.txt').exists())

    def test_plan_init_creates_pending_state(self):
        project, plan, _ = self.plan_fixture()
        self.success(self.plan_command(project, 'init'))
        self.assertEqual({key: row['status'] for key, row in self.state(plan)['tasks'].items()},
                         {'A': 'pending', 'B': 'pending', 'C': 'pending'})

    def test_plan_init_preserves_existing_state(self):
        project, plan, _ = self.initialized_plan()
        self.success(self.plan_command(project, 'start', 'A'))
        before = (plan / 'state.json').read_bytes()
        self.success(self.plan_command(project, 'init'))
        self.assertEqual((plan / 'state.json').read_bytes(), before)

    def test_plan_start_rejects_unfinished_dependency(self):
        project, plan, _ = self.initialized_plan()
        before = (plan / 'state.json').read_bytes()
        self.failure(self.plan_command(project, 'start', 'B'))
        self.assertEqual((plan / 'state.json').read_bytes(), before)

    def test_plan_complete_requires_evidence_argument(self):
        project, plan, _ = self.initialized_plan()
        self.success(self.plan_command(project, 'start', 'A'))
        before = (plan / 'state.json').read_bytes()
        self.failure(self.plan_command(project, 'complete', 'A', '--command', 'fixture'))
        self.assertEqual((plan / 'state.json').read_bytes(), before)

    def test_plan_complete_rejects_empty_evidence(self):
        project, plan, _ = self.initialized_plan()
        self.success(self.plan_command(project, 'start', 'A'))
        (project / 'empty.txt').write_bytes(b'')
        before = (plan / 'state.json').read_bytes()
        self.failure(self.plan_command(project, 'complete', 'A', '--command', 'fixture', '--evidence', 'empty.txt'))
        self.assertEqual((plan / 'state.json').read_bytes(), before)

    def test_plan_complete_records_existing_evidence_hash(self):
        project, plan, _ = self.initialized_plan()
        self.complete_fixture_task(project, 'A')
        row = self.state(plan)['tasks']['A']
        self.assertEqual(row['status'], 'completed')
        self.assertEqual(row['evidence'][0]['sha256'], hashlib.sha256((project / 'evidence.txt').read_bytes()).hexdigest())

    def test_plan_reopen_invalidates_transitive_dependents(self):
        project, plan, _ = self.initialized_plan()
        for task in ('A', 'B', 'C'):
            self.complete_fixture_task(project, task)
        self.success(self.plan_command(project, 'reopen', 'A', '--note', 'input changed'))
        self.assertEqual({key: row['status'] for key, row in self.state(plan)['tasks'].items()},
                         {'A': 'pending', 'B': 'pending', 'C': 'pending'})

    def test_plan_cannot_block_completed_prerequisite_without_reopen(self):
        project, plan, _ = self.initialized_plan()
        for task in ('A', 'B', 'C'):
            self.complete_fixture_task(project, task)
        before = (plan / 'state.json').read_bytes()
        self.failure(self.plan_command(project, 'block', 'A', '--note', 'new failure found'))
        self.assertEqual((plan / 'state.json').read_bytes(), before)

    def test_plan_verify_evidence_rejects_external_symlink_substitution(self):
        project, _, _ = self.initialized_plan()
        self.complete_fixture_task(project, 'A')
        evidence = project / 'evidence.txt'
        outside = self.temp / 'outside-evidence.txt'
        outside.write_bytes(evidence.read_bytes())
        evidence.unlink()
        evidence.symlink_to(outside)
        self.failure(self.plan_command(project, 'verify-evidence'))

    def test_plan_refuses_symlink_metadata_directory_and_outside_writes(self):
        project, plan, _ = self.plan_fixture()
        outside_plan = self.temp / 'outside-plan'
        plan.rename(outside_plan)
        plan.symlink_to(outside_plan, target_is_directory=True)
        self.failure(self.plan_command(project, 'init'))
        self.assertFalse((outside_plan / 'state.json').exists())
        self.assertFalse((outside_plan / 'state.lock').exists())


if __name__ == '__main__':
    unittest.main()
