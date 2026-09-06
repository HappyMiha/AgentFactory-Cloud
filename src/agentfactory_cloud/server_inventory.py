"""Read-only development-node inventory, separate from execution qualification.

Core owns hardware observations. Cloud adds a redacted host-profile envelope and
explicit gaps; an inventory cannot authorize a worker or a hosted deployment.
"""
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import platform
import re
import socket
import stat

from agent_factory.hardware_inventory import collect_inventory


PROFILE = 'development-node-inventory-v1'
_LOCAL_LINUX_FS = frozenset({'ext2', 'ext3', 'ext4', 'btrfs', 'xfs', 'tmpfs',
                           'ramfs', 'f2fs', 'jfs', 'reiserfs', 'zfs'})


class LocalWorkspaceRequired(ValueError):
    def __init__(self):
        super().__init__('Select an existing directory on a verified local volume without links.')


def _linux_mounts():
    # Kernel metadata only; do not ask a candidate filesystem about its type.
    with open('/proc/self/mountinfo', 'rb') as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise LocalWorkspaceRequired()
    mounts = []
    for line in raw.decode('utf-8', errors='strict').splitlines():
        left, right = line.split(' - ', 1)
        fields, filesystem = left.split(), right.split()[0]
        mount = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), fields[4])
        if not mount.startswith('/'):
            raise LocalWorkspaceRequired()
        mounts.append((PurePosixPath(mount), filesystem))
    return mounts


def _windows_drive_type(root):
    import ctypes
    query = ctypes.WinDLL('kernel32', use_last_error=True).GetDriveTypeW
    query.argtypes = [ctypes.c_wchar_p]
    query.restype = ctypes.c_uint
    return query(root)


def local_workspace(workspace):
    """Classify lexically before metadata lookup, then reject every link parent.

    This is a trusted local operator boundary, not isolation from an administrator
    concurrently changing mount points. Unknown filesystem/platform types fail
    closed. No realpath/resolve, directory traversal or remote volume probe occurs
    before the drive/mount classification.
    """
    try:
        raw = os.fspath(workspace)
        if (not isinstance(raw, str) or not raw or len(raw) > 4096
                or any(ord(c) < 32 for c in raw) or raw.startswith(('//', '\\\\'))):
            raise LocalWorkspaceRequired()
        system = platform.system()
        if system == 'Windows':
            if '..' in PureWindowsPath(raw).parts:
                raise LocalWorkspaceRequired()
            drive, tail = ntpath.splitdrive(raw)
            if drive and (not re.fullmatch('[A-Za-z]:', drive) or not tail.startswith(('\\', '/'))):
                raise LocalWorkspaceRequired()
            if not drive:
                if raw.startswith(('\\', '/')):
                    raise LocalWorkspaceRequired()
                raw = ntpath.join(os.getcwd(), raw)
            path = PureWindowsPath(raw)
            if (not re.fullmatch('[A-Za-z]:', path.drive) or not path.is_absolute()
                    or any(':' in part or part.endswith((' ', '.')) for part in path.parts[1:])):
                raise LocalWorkspaceRequired()
            # Reject unknown/no-root and remote mapped drives before lstat.
            if _windows_drive_type(path.anchor) not in {2, 3, 5, 6}:
                raise LocalWorkspaceRequired()
        elif system == 'Linux':
            if '\\' in raw or ':' in raw or '..' in PurePosixPath(raw).parts:
                raise LocalWorkspaceRequired()
            path = PurePosixPath(raw)
            if not path.is_absolute():
                path = PurePosixPath(os.getcwd()) / path  # lexical only
            mounts = _linux_mounts()
            covering = [(mount, fs) for mount, fs in mounts if path.is_relative_to(mount)]
            if (not any(mount == PurePosixPath('/') for mount, _ in covering)
                    or any(fs not in _LOCAL_LINUX_FS for _, fs in covering)):
                raise LocalWorkspaceRequired()
        else:
            raise LocalWorkspaceRequired()
        if len(path.parts) > 256:
            raise LocalWorkspaceRequired()
        # Inspect one component at a time without following it. Never inspect a
        # child below an unchecked symlink, junction, mount point or placeholder.
        for parent in [*reversed(path.parents), path]:
            entry = os.lstat(str(parent))
            if not stat.S_ISDIR(entry.st_mode) or stat.S_ISLNK(entry.st_mode):
                raise LocalWorkspaceRequired()
            if system == 'Windows':
                attributes = getattr(entry, 'st_file_attributes', None)
                if attributes is None or attributes & 0x400:  # FILE_ATTRIBUTE_REPARSE_POINT
                    raise LocalWorkspaceRequired()
        return Path(str(path))
    except (OSError, ValueError, TypeError, IndexError, AttributeError):
        raise LocalWorkspaceRequired() from None


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
    hardware = collect_inventory(local_workspace(workspace))
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
