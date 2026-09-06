"""Read-only development-node inventory, separate from execution qualification.

Core owns hardware observations. Cloud adds a redacted host-profile envelope and
explicit gaps; an inventory cannot authorize a worker or a hosted deployment.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import socket

from agent_factory.hardware_inventory import collect_inventory


PROFILE = 'development-node-inventory-v1'


def _kernel_tokens(path):
    """Fixed local kernel files only; never return their raw contents."""
    try:
        with path.open('rb') as stream:
            data = stream.read(32769)
        if len(data) > 32768:
            return None
        return set(data.decode('ascii', errors='replace').split())
    except OSError:
        return None


def _host_observations():
    network = {'interface_count': None, 'boundary_verified': False}
    try:
        # Count only: no addresses, interface names, routes or listener details.
        network['interface_count'] = len(socket.if_nameindex())
    except (OSError, AttributeError):
        pass
    virtualization = {
        'cpu_virtualization_flag': None, 'kvm_device_present': None,
        'cgroup_v2_present': None, 'sandbox_qualified': False,
    }
    if platform.system() == 'Linux':
        flags = _kernel_tokens(Path('/proc/cpuinfo'))
        if flags is not None:
            virtualization['cpu_virtualization_flag'] = bool({'vmx', 'svm'} & flags)
        for key, path in (
            ('kvm_device_present', '/dev/kvm'),
            ('cgroup_v2_present', '/sys/fs/cgroup/cgroup.controllers'),
        ):
            try:
                virtualization[key] = Path(path).exists()
            except OSError:
                pass
    return network, virtualization


def inventory(workspace):
    """Observe this explicitly selected development node; never contact a peer.

    The caller provides its configured local workspace volume. Core's bounded
    fixed OS/GPU probes are the only subprocesses. No toolchain, provider, daemon,
    network port scan, installation or generated workload is started here.
    """
    hardware = collect_inventory(Path(workspace))
    network, virtualization = _host_observations()
    observations = {'hardware': hardware, 'network': network,
                    'virtualization': virtualization}
    raw = json.dumps(observations, sort_keys=True, separators=(',', ':'),
                     allow_nan=False).encode('utf-8')
    return {
        'schema_version': 1, 'profile': PROFILE,
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'target_kind': 'development_node',
        'observations': observations,
        'observations_sha256': hashlib.sha256(raw).hexdigest(),
        'capacity_decision': 'blocked',
        'qualified_capabilities': [],
        'execution_eligible': False,
        'gaps': [
            'Toolchain presence is not a tested version or build capability.',
            'Measured free RAM, per-device VRAM and disk are a snapshot, not reserved capacity.',
            'Network/service boundaries, access roles and backup recovery are unverified.',
            'Virtualization flags and device presence do not qualify workload isolation.',
            'Worker identity, Core scheduling admission and synthetic fault drills remain required.',
        ],
        'reported_server': {'status': 'unknown', 'inventory_available': False,
                            'deployment_authorized': False},
    }
