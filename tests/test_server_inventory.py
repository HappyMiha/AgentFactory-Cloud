import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from agentfactory_cloud import server_inventory as module


class ServerInventoryTests(unittest.TestCase):
    def test_inventory_preserves_core_unknowns_and_separate_gpu_capacity(self):
        hardware = {'memory': {'free_bytes': None}, 'disk': {'free_bytes': 0},
                    'gpus': [{'dedicated_total_bytes': 8 * 1024**3},
                             {'dedicated_total_bytes': 8 * 1024**3}],
                    'software': [{'id': 'godot', 'status': 'detected', 'version': None}]}
        with patch.object(module, 'collect_inventory', return_value=hardware) as collect:
            report = module.inventory(Path('.'))
        collect.assert_called_once_with(Path('.'))
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
        source = Path(__file__).resolve().parents[1] / 'scripts' / 'qualify_workers.py'
        spec = importlib.util.spec_from_file_location('qualify_workers_test', source)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
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


if __name__ == '__main__':
    unittest.main()
