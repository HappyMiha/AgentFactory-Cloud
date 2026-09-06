import hashlib
import io
from pathlib import Path
import socket
import stat
import sys
import threading
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from agentfactory_cloud.upload_inspection import (
    ClamdScanner, InspectionBlocked, MAX_BYTES, inspect_upload, safe_path,
)


class TestScanner:
    """Structural unit fixture only; actual clamd tests are separate."""
    def scan(self, data):
        return {'verdict': 'clear', 'sha256': hashlib.sha256(data).hexdigest()}


def archive(entries, **kwargs):
    target = io.BytesIO()
    with zipfile.ZipFile(target, 'w', **kwargs) as z:
        for name, data in entries:
            z.writestr(name, data)
    return target.getvalue()


class UploadInspectionTests(unittest.TestCase):
    def inspect(self, data=b'hello', path='src/game.txt', media_type='text/plain', scanner=TestScanner()):
        return inspect_upload(data, path, media_type, scanner)

    def test_path_traversal_and_portable_aliases_are_blocked(self):
        for name in ('../secret', '/root/file', 'a/../b', 'a//b', 'a\\b', 'C:foo',
                     'CON.txt', 'aux', 'foo.', 'foo ', 'x\x00y', 'x\ny'):
            with self.subTest(name=name), self.assertRaises(InspectionBlocked):
                safe_path(name)
        self.assertEqual(safe_path('гра/текст.txt'), 'гра/текст.txt')

    def test_missing_malformed_or_wrong_digest_scan_blocks(self):
        with self.assertRaises(InspectionBlocked): self.inspect(scanner=None)
        class Wrong:
            def scan(self, data): return {'verdict': 'clear', 'sha256': '0'*64}
        with self.assertRaises(InspectionBlocked): self.inspect(scanner=Wrong())

    def test_size_and_media_bounds(self):
        for data in (b'', b'x'*(MAX_BYTES+1), 'text'):
            with self.assertRaises(InspectionBlocked): self.inspect(data)
        with self.assertRaises(InspectionBlocked): self.inspect(media_type='text/html')

    def test_valid_zip_inspects_without_extracting(self):
        result = self.inspect(archive([('src/main.gd', 'print("hello")'), ('assets/coin.txt', 'coin')]), 'source.zip', 'application/zip')
        self.assertEqual(result['policy'], 'bounded-clamd-v1')

    def test_zip_traversal_links_duplicates_and_bombs_block(self):
        link = zipfile.ZipInfo('link'); link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        bad = [archive([('../x', b'x')]), archive([(link, b'../secret')]),
               archive([('A', b'x'), ('a', b'y')]),
               archive([('huge', b'x'*1024*1024)], compression=zipfile.ZIP_DEFLATED),
               archive([(str(n), b'x') for n in range(257)]),
               archive([('nested', archive([('x', b'x')]))]),
               archive([('nested-sfx', b'MZprefix'+archive([('x', b'x')]))]), b'PKbroken']
        for data in bad:
            with self.subTest(size=len(data)), self.assertRaises(InspectionBlocked):
                self.inspect(data, 'upload.zip', 'application/zip')

    def test_unsupported_archives_cannot_hide_under_plain_media(self):
        for data, name in [(b'\x1f\x8bxxx','x'), (b'Rar!xxx','x'), (b'bytes','x.tar'),
                           (b'BZhxxx','x'), (b'\xfd7zXZ\0xxx','x'),
                           (b'MZprefix'+archive([('x',b'x')]),'x.bin')]:
            with self.assertRaises(InspectionBlocked): self.inspect(data, name)

    def test_unavailable_and_stale_real_protocol_responses_block(self):
        with socket.socket() as server:
            server.bind(('127.0.0.1', 0)); server.listen()
            port = server.getsockname()[1]
            def stale():
                with server.accept()[0] as connection:
                    connection.recv(128)
                    connection.sendall(b'ClamAV 1.4.6/1/Mon Jan 01 00:00:00 2024\0')
            thread = threading.Thread(target=stale); thread.start()
            with self.assertRaisesRegex(InspectionBlocked, 'stale'):
                ClamdScanner(port).scan(b'hello')
            thread.join(2)
        with self.assertRaises(InspectionBlocked): ClamdScanner(port, timeout=0.2).scan(b'hello')
