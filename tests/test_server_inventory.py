import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from agentfactory_cloud import server_inventory as module


class ServerInventoryTests(unittest.TestCase):
    def load_cli(self):
        source = Path(__file__).resolve().parents[1] / 'scripts' / 'qualify_workers.py'
        spec = importlib.util.spec_from_file_location('qualify_workers_test', source)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        return cli

    def test_inventory_preserves_core_unknowns_and_separate_gpu_capacity(self):
        hardware = {'memory': {'free_bytes': None}, 'disk': {'free_bytes': 0},
                    'gpus': [{'dedicated_total_bytes': 8 * 1024**3},
                             {'dedicated_total_bytes': 8 * 1024**3}],
                    'software': [{'id': 'godot', 'status': 'detected', 'version': None}]}
        with patch.object(module, 'collect_inventory', return_value=hardware) as collect:
            report = module.inventory(Path('.'))
        collect.assert_called_once_with(Path.cwd())
        self.assertEqual(report['observations']['hardware'], hardware)
        self.assertFalse(report['execution_eligible'])
        self.assertEqual(report['capacity_decision'], 'blocked')
        self.assertEqual(report['qualified_capabilities'], [])
        self.assertEqual(report['reported_server']['status'], 'unknown')
        raw = json.dumps(report['observations'], sort_keys=True, separators=(',', ':'),
                         allow_nan=False).encode()
        self.assertEqual(report['observations_sha256'], hashlib.sha256(raw).hexdigest())

    def test_network_omits_names_and_does_not_infer_boundary(self):
        with patch.object(module.socket, 'if_nameindex', return_value=[(1, 'private-interface')]), \
                patch.object(module.platform, 'system', return_value='Windows'):
            network, virtualization = module._host_observations()
        self.assertEqual(network, {'interface_count': 1, 'boundary_verified': False})
        self.assertNotIn('private-interface', json.dumps(network))
        self.assertIsNone(virtualization['cpu_virtualization_flag'])
        self.assertFalse(virtualization['sandbox_qualified'])

    def test_permission_failure_is_unknown_without_raw_error(self):
        with patch.object(module.socket, 'if_nameindex', side_effect=PermissionError('private-path')), \
                patch.object(module.platform, 'system', return_value='Other'):
            network, virtualization = module._host_observations()
        self.assertIsNone(network['interface_count'])
        self.assertNotIn('private-path', json.dumps([network, virtualization]))

    def test_kernel_input_limit_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixed-kernel-fixture'
            self.assertIsNone(module._kernel_tokens(path))
            path.write_bytes(b'flags : vmx other')
            self.assertIn('vmx', module._kernel_tokens(path))
            path.write_bytes(b'x' * 32769)
            self.assertIsNone(module._kernel_tokens(path))

    def test_linux_signals_still_do_not_qualify_sandbox(self):
        with patch.object(module.platform, 'system', return_value='Linux'), \
                patch.object(module, '_kernel_tokens', return_value={'vmx'}), \
                patch.object(module.Path, 'exists', return_value=True):
            _, virtualization = module._host_observations()
        self.assertTrue(virtualization['cpu_virtualization_flag'])
        self.assertTrue(virtualization['kvm_device_present'])
        self.assertTrue(virtualization['cgroup_v2_present'])
        self.assertFalse(virtualization['sandbox_qualified'])

    def test_cli_creates_private_evidence_and_refuses_overwrite(self):
        cli = self.load_cli()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'inventory.json'
            argv = ['qualify_workers', 'inventory', '--workspace', directory,
                    '--output', str(output)]
            with patch.object(cli, 'inventory', return_value={'execution_eligible': False}), \
                    patch.object(cli.sys, 'argv', argv), redirect_stdout(io.StringIO()):
                cli.main()
                before = output.read_bytes()
                self.assertEqual(json.loads(before), {'execution_eligible': False})
                if os.name == 'posix':
                    self.assertEqual(output.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError):
                    cli.main()
                self.assertEqual(output.read_bytes(), before)

    def test_unc_and_device_paths_reject_before_any_path_lookup_or_collection(self):
        for path in [r'\\server\share\workspace', '//server/share/workspace',
                     r'\\?\UNC\server\share', r'\\.\C:\workspace']:
            with self.subTest(path=path), patch.object(module.os, 'lstat') as lookup, \
                    patch.object(module, 'collect_inventory') as collect, \
                    patch.object(module, '_linux_mounts') as mounts, \
                    patch.object(module, '_windows_drive_type') as drive:
                with self.assertRaises(module.LocalWorkspaceRequired): module.inventory(path)
                lookup.assert_not_called(); collect.assert_not_called()
                mounts.assert_not_called(); drive.assert_not_called()

    def test_windows_remote_or_unknown_drive_rejects_before_directory_lookup(self):
        for kind in [0, 1, 4]:
            with self.subTest(kind=kind), patch.object(module.platform, 'system', return_value='Windows'), \
                    patch.object(module, '_windows_drive_type', return_value=kind) as drive, \
                    patch.object(module.os, 'lstat') as lookup, \
                    patch.object(module, 'collect_inventory') as collect:
                with self.assertRaises(module.LocalWorkspaceRequired): module.inventory(r'Z:\workspace')
                drive.assert_called_once_with('Z:\\')
                lookup.assert_not_called(); collect.assert_not_called()

    def test_windows_reparse_parent_stops_before_child_lookup(self):
        normal = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x10)
        reparse = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x410)
        with patch.object(module.platform, 'system', return_value='Windows'), \
                patch.object(module, '_windows_drive_type', return_value=3), \
                patch.object(module.os, 'lstat', side_effect=[normal, reparse]) as lookup, \
                patch.object(module, 'collect_inventory') as collect:
            with self.assertRaises(module.LocalWorkspaceRequired): module.inventory(r'C:\junction\child')
            self.assertEqual([c.args[0] for c in lookup.call_args_list], ['C:\\', r'C:\junction'])
            collect.assert_not_called()

    def test_windows_local_directory_is_checked_parent_first(self):
        normal = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x10)
        with patch.object(module.platform, 'system', return_value='Windows'), \
                patch.object(module, '_windows_drive_type', return_value=3), \
                patch.object(module.os, 'lstat', return_value=normal) as lookup:
            self.assertEqual(str(module.local_workspace(r'C:\local\child')), r'C:\local\child')
            self.assertEqual([c.args[0] for c in lookup.call_args_list], ['C:\\', r'C:\local', r'C:\local\child'])

    def test_windows_ambiguous_paths_reject_before_volume_lookup(self):
        for path in [r'C:relative', r'\root-relative', r'C:\safe\..\remote', r'C:\safe.\child', r'C:\safe:stream']:
            with self.subTest(path=path), patch.object(module.platform, 'system', return_value='Windows'), \
                    patch.object(module, '_windows_drive_type') as drive, patch.object(module.os, 'lstat') as lookup:
                with self.assertRaises(module.LocalWorkspaceRequired): module.local_workspace(path)
                drive.assert_not_called(); lookup.assert_not_called()

    def test_linux_remote_autofs_and_unknown_mount_reject_without_path_lookup(self):
        for fs in ['cifs', 'nfs', 'nfs4', 'autofs', 'fuse.sshfs', 'overlay', 'unknown']:
            mounts = [(PurePosixPath('/'), 'ext4'), (PurePosixPath('/mnt/remote'), fs)]
            with self.subTest(fs=fs), patch.object(module.platform, 'system', return_value='Linux'), \
                    patch.object(module, '_linux_mounts', return_value=mounts), \
                    patch.object(module.os, 'lstat') as lookup, patch.object(module, 'collect_inventory') as collect:
                with self.assertRaises(module.LocalWorkspaceRequired): module.inventory('/mnt/remote/child')
                lookup.assert_not_called(); collect.assert_not_called()

    def test_linux_link_parent_stops_before_following_target(self):
        normal = SimpleNamespace(st_mode=stat.S_IFDIR)
        link = SimpleNamespace(st_mode=stat.S_IFLNK)
        with patch.object(module.platform, 'system', return_value='Linux'), \
                patch.object(module, '_linux_mounts', return_value=[(PurePosixPath('/'), 'ext4')]), \
                patch.object(module.os, 'lstat', side_effect=[normal, link]) as lookup, \
                patch.object(module, 'collect_inventory') as collect:
            with self.assertRaises(module.LocalWorkspaceRequired): module.inventory('/link/remote/child')
            self.assertEqual([c.args[0] for c in lookup.call_args_list], ['/', '/link'])
            collect.assert_not_called()

    def test_linux_component_match_does_not_confuse_remote_mount_prefix(self):
        mounts = [(PurePosixPath('/'), 'ext4'), (PurePosixPath('/work'), 'cifs')]
        with patch.object(module.platform, 'system', return_value='Linux'), \
                patch.object(module, '_linux_mounts', return_value=mounts), \
                patch.object(module.os, 'lstat', return_value=SimpleNamespace(st_mode=stat.S_IFDIR)):
            self.assertEqual(module.local_workspace('/workspace').as_posix(), '/workspace')

    def test_mount_metadata_failure_rejects_without_lookup_or_private_error(self):
        for failure in [PermissionError('private mount metadata'), ValueError('private malformed mount')]:
            with patch.object(module.platform, 'system', return_value='Linux'), \
                    patch.object(module, '_linux_mounts', side_effect=failure), \
                    patch.object(module.os, 'lstat') as lookup:
                with self.assertRaises(module.LocalWorkspaceRequired) as caught: module.local_workspace('/local')
                self.assertNotIn('private', str(caught.exception)); lookup.assert_not_called()

    def test_mount_parser_decodes_space_and_rejects_oversize_metadata(self):
        table = b'1 0 8:1 / / rw - ext4 /dev/example rw\n2 1 0:1 / /mnt/remote\\040folder rw - cifs //server/share rw\n'
        with patch('builtins.open', return_value=io.BytesIO(table)):
            self.assertEqual(module._linux_mounts(), [(PurePosixPath('/'), 'ext4'), (PurePosixPath('/mnt/remote folder'), 'cifs')])
        with patch('builtins.open', return_value=io.BytesIO(b'x' * (1024 * 1024 + 1))):
            with self.assertRaises(module.LocalWorkspaceRequired): module._linux_mounts()

    def test_cli_rejects_unc_before_directory_lookup_collection_and_output(self):
        cli = self.load_cli()
        with patch.object(cli.sys, 'argv', ['qualify_workers', 'inventory', '--workspace',
                r'\\server\share\workspace', '--output', 'unused.json']), \
                patch.object(module.os, 'lstat') as lookup, patch.object(module, 'collect_inventory') as collect, \
                patch.object(module.Path, 'is_dir', side_effect=AssertionError('Unsafe directory lookup')) as is_dir, \
                patch.object(module.Path, 'stat', side_effect=AssertionError('Unsafe target stat')) as target_stat, \
                patch.object(cli.os, 'open') as output, patch.object(cli.sys, 'stderr', io.StringIO()):
            with self.assertRaises(SystemExit) as caught: cli.main()
            self.assertEqual(caught.exception.code, 2)
            lookup.assert_not_called(); collect.assert_not_called(); output.assert_not_called()
            is_dir.assert_not_called(); target_stat.assert_not_called()


if __name__ == '__main__':
    unittest.main()
