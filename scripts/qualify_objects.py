#!/usr/bin/env python3
"""Start/stop only recorded disposable Cloud023 Docker services on loopback."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import threading
import time
import uuid


IMAGES = {
    's3': 'quay.io/minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e',
    'clamd': 'clamav/clamav@sha256:b25d9199257ae7ef45e0cc4c7eaa60ce7e5447796f0090d5ff311d1a30980cc3',
    'postgres': 'postgres:17.11',
}


def docker(*args):
    return subprocess.check_output(['docker', *args], text=True).strip()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        stream.write(value)


def audit_server(root):
    """Persist a strict field allowlist; never write authorization headers or identities."""
    config = json.loads((root/'audit-config.json').read_text())
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            if self.path != '/audit' or not secrets.compare_digest(self.headers.get('Authorization', ''), config['token']):
                self.send_error(403); return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 1024*1024:
                    raise ValueError('Audit request size')
                value = json.loads(self.rfile.read(size))
                entries = value if isinstance(value, list) else [value]
                rows = []
                for entry in entries:
                    api = entry.get('api', {})
                    rows.append({'time': entry.get('time'), 'request_id': entry.get('requestID'),
                                 'api': api.get('name'), 'bucket': api.get('bucket'),
                                 'status_code': api.get('statusCode')})
                with lock, (root/'s3-access.jsonl').open('a', encoding='utf-8') as stream:
                    os.chmod(root/'s3-access.jsonl', 0o600)
                    for row in rows:
                        stream.write(json.dumps(row)+'\n')
                self.send_response(200); self.end_headers()
            except (ValueError, TypeError, AttributeError):
                self.send_error(400)
    # Linux Docker bridge only, not the LAN or wildcard interface.
    server = ThreadingHTTPServer((config['host'], 0), Handler)
    save(root/'audit-ready.json', json.dumps({'port': server.server_port, 'pid': os.getpid()}))
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'stop', 'audit'])
    parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args()
    root = args.work.resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if args.action == 'audit':
        audit_server(root)
        return
    record = root / 'containers.json'
    if args.action == 'stop':
        state = json.loads(record.read_text())
        for name in state['names']:
            if not name.startswith('cloud023-test-'):
                raise ValueError('Refusing unrelated container cleanup')
            subprocess.run(['docker', 'stop', name], check=True, stdout=subprocess.DEVNULL)
        pid = state.get('audit_pid')
        if pid:
            proc = Path(f'/proc/{pid}/cmdline')
            if proc.exists():
                command = proc.read_bytes().split(b'\0')
                if str(Path(__file__).resolve()).encode() not in command or str(root).encode() not in command:
                    raise ValueError('Recorded audit PID belongs to a different process')
                os.kill(pid, signal.SIGTERM)
        for name in ('services.json', 'postgres.env', 's3.env', 'containers.json', 'audit-config.json', 'audit-ready.json'):
            (root / name).unlink(missing_ok=True)
        print('Recorded disposable services stopped; credentials removed.')
        return
    if record.exists() or (root / 'services.json').exists():
        raise ValueError('Existing qualification state; inspect it instead of overwriting')
    suffix = uuid.uuid4().hex[:12]
    pg_password, s3_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    save(root / 'postgres.env', 'POSTGRES_PASSWORD=' + pg_password + '\n')
    save(root / 's3.env', 'MINIO_ROOT_USER=cloud023-test-admin\nMINIO_ROOT_PASSWORD=' + s3_password + '\n')
    state = {'names': [], 'images': IMAGES}
    save(record, json.dumps(state))
    gateway = json.loads(docker('network', 'inspect', 'bridge'))[0]['IPAM']['Config'][0]['Gateway']
    token = 'Bearer ' + secrets.token_urlsafe(32)
    save(root/'audit-config.json', json.dumps({'host': gateway, 'token': token}))
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'audit', '--work', str(root)],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    state['audit_pid'] = process.pid
    record.write_text(json.dumps(state))
    deadline = time.monotonic()+5
    while not (root/'audit-ready.json').exists():
        if process.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError('Audit collector did not start; inspect recorded state')
        time.sleep(0.05)
    audit_port = json.loads((root/'audit-ready.json').read_text())['port']
    with (root/'s3.env').open('a') as stream:
        stream.write(f'MINIO_AUDIT_WEBHOOK_ENABLE_CLOUD023=on\nMINIO_AUDIT_WEBHOOK_ENDPOINT_CLOUD023=http://{gateway}:{audit_port}/audit\nMINIO_AUDIT_WEBHOOK_AUTH_TOKEN_CLOUD023={token}\n')

    def start(kind, port, extra, command):
        name = 'cloud023-test-' + suffix + '-' + kind
        docker('run', '-d', '--rm', '--name', name, '--label', 'agentfactory.task=cloud:AF-CLD-023',
               '-p', f'127.0.0.1::{port}', *extra, IMAGES[kind], *command)
        state['names'].append(name)
        record.write_text(json.dumps(state))
        mapping = json.loads(docker('inspect', '--format', '{{json .NetworkSettings.Ports}}', name))
        return int(mapping[str(port)+'/tcp'][0]['HostPort'])

    # No host directories, Docker socket or production data are mounted.
    pg_port = start('postgres', 5432, ['--memory', '512m', '--cpus', '1', '--tmpfs', '/var/lib/postgresql/data:rw,size=512m',
                                    '--env-file', str(root/'postgres.env')], [])
    s3_port = start('s3', 9000, ['--memory', '512m', '--cpus', '1', '--tmpfs', '/data:rw,size=128m',
                              '--env-file', str(root/'s3.env')], ['server', '/data', '--console-address', ':9001'])
    clam_port = start('clamd', 3310, ['--memory', '4g', '--cpus', '2', '-e', 'TZ=UTC'], [])
    save(root/'services.json', json.dumps({
        'postgres': {'host': '127.0.0.1', 'port': pg_port, 'user': 'postgres', 'password': pg_password},
        's3': {'endpoint': f'http://127.0.0.1:{s3_port}', 'access_key': 'cloud023-test-admin', 'secret_key': s3_password},
        'clamd_port': clam_port,
        'audit_log': str(root/'s3-access.jsonl'),
    }))
    print('Disposable services started. Private configuration: ' + str(root/'services.json'))
    print('Wait for service readiness before tests; an unavailable or stale scanner blocks uploads.')


if __name__ == '__main__':
    main()
