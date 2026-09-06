#!/usr/bin/env python3
"""Collect an explicit local lab inventory; later qualification is separate."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agentfactory_cloud.server_inventory import inventory, LocalWorkspaceRequired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inventory'])
    parser.add_argument('--workspace', required=True,
                        help='Configured local development workspace volume')
    parser.add_argument('--output', required=True, type=Path,
                        help='New private local evidence file; existing files are never replaced')
    args = parser.parse_args()
    try:
        document = inventory(args.workspace)
    except LocalWorkspaceRequired as exc:
        parser.error(str(exc))
    payload = json.dumps(document, ensure_ascii=True, indent=2) + '\n'
    # The operator selects the local destination. Exclusive create also rejects
    # an existing symlink. Keep node details out of Git and the message bus.
    with os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                   'w', encoding='utf-8') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    print('Development-node inventory recorded; execution and reported server remain blocked.')


if __name__ == '__main__':
    main()
