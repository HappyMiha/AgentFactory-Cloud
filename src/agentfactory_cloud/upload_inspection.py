"""Bounded in-memory inspection. Nothing is extracted or executed."""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import io
import re
import socket
import stat
import struct
import time
import zipfile
import zlib


MAX_BYTES = 8 * 1024 * 1024
MAX_EXPANDED = 32 * 1024 * 1024
MEDIA = {'text/plain', 'application/json', 'application/zip', 'application/octet-stream',
         'image/png', 'image/jpeg', 'audio/ogg', 'audio/wav'}
ARCHIVE_MAGIC = (b'\x1f\x8b', b'7z\xbc\xaf', b'Rar!', b'BZh', b'\xfd7zXZ\0')


class InspectionBlocked(ValueError):
    pass


def safe_path(value):
    if (not isinstance(value, str) or not 1 <= len(value.encode('utf-8')) <= 240
            or value.startswith('/') or '\\' in value or ':' in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise InspectionBlocked('Unsafe object path')
    parts = value.split('/')
    if any(p in ('', '.', '..') or p.endswith((' ', '.')) for p in parts):
        raise InspectionBlocked('Unsafe object path')
    if any(re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', p) for p in parts):
        raise InspectionBlocked('Reserved object path')
    return value


def inspect_archive(data):
    if not data.startswith(b'PK\x03\x04'):
        raise InspectionBlocked('Only bounded, nonempty ZIP archives are supported')
    expanded = 0
    names = set()
    deadline = time.monotonic() + 5
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if not 1 <= len(entries) <= 256:
                raise InspectionBlocked('Archive entry limit')
            for entry in entries:
                name = safe_path(entry.filename.rstrip('/') if entry.is_dir() else entry.filename)
                if name.casefold() in names or entry.flag_bits & 1:
                    raise InspectionBlocked('Duplicate or encrypted archive entry')
                names.add(name.casefold())
                mode = stat.S_IFMT(entry.external_attr >> 16)
                if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise InspectionBlocked('Archive links and devices are blocked')
                if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise InspectionBlocked('Unsupported archive compression')
                expanded += entry.file_size
                if (expanded > MAX_EXPANDED or entry.file_size > MAX_BYTES
                        or entry.file_size > max(1, entry.compress_size) * 100):
                    raise InspectionBlocked('Archive expansion limit')
                with archive.open(entry) as stream:
                    read_size = 0
                    contents = bytearray()
                    while chunk := stream.read(65536):
                        read_size += len(chunk)
                        if time.monotonic() > deadline or read_size > entry.file_size:
                            raise InspectionBlocked('Archive inspection limit')
                        contents.extend(chunk)
                    if (contents.startswith(ARCHIVE_MAGIC) or contents[257:262] == b'ustar'
                            or zipfile.is_zipfile(io.BytesIO(contents))):
                        raise InspectionBlocked('Nested archives are blocked')
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, zlib.error) as exc:
        raise InspectionBlocked('Malformed or unsupported archive') from exc


@dataclass(frozen=True)
class ClamdScanner:
    # The first qualified profile uses a separately isolated local daemon only.
    port: int
    timeout: float = 10

    def _connect(self):
        return socket.create_connection(('127.0.0.1', self.port), timeout=self.timeout)

    @staticmethod
    def _response(connection):
        result = b''
        while b'\0' not in result and len(result) <= 4096:
            part = connection.recv(1024)
            if not part:
                break
            result += part
        if not result.endswith(b'\0') or len(result) > 4096:
            raise InspectionBlocked('Invalid malware scanner response')
        return result[:-1].decode('ascii', errors='strict')

    def scan(self, data):
        try:
            with self._connect() as connection:
                connection.sendall(b'zVERSION\0')
                version = self._response(connection)
            parts = version.split('/')
            if len(parts) != 3 or not parts[0].startswith('ClamAV ') or not parts[1].isdigit():
                raise InspectionBlocked('Unqualified malware scanner version')
            signature_time = datetime.strptime(parts[2], '%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - signature_time
            if not timedelta(minutes=-5) <= age <= timedelta(days=7):
                raise InspectionBlocked('Malware signatures are stale')
            with self._connect() as connection:
                connection.sendall(b'zINSTREAM\0')
                for offset in range(0, len(data), 65536):
                    chunk = data[offset:offset+65536]
                    connection.sendall(struct.pack('!I', len(chunk)) + chunk)
                connection.sendall(b'\0\0\0\0')
                response = self._response(connection)
            if response != 'stream: OK':
                raise InspectionBlocked('Malware policy blocked upload')
            return {'engine': parts[0], 'signature_version': parts[1],
                    'signature_date': signature_time.isoformat(), 'verdict': 'clear',
                    'sha256': hashlib.sha256(data).hexdigest()}
        except (OSError, UnicodeError, ValueError) as exc:
            if isinstance(exc, InspectionBlocked):
                raise
            raise InspectionBlocked('Malware inspection unavailable') from exc


def inspect_upload(data, path, media_type, scanner):
    safe_path(path)
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_BYTES:
        raise InspectionBlocked('Upload must contain 1 byte to 8 MiB')
    if media_type not in MEDIA:
        raise InspectionBlocked('Unsupported media type')
    is_zip = data.startswith(b'PK') or zipfile.is_zipfile(io.BytesIO(data)) or path.lower().endswith('.zip') or media_type == 'application/zip'
    if is_zip:
        inspect_archive(data)
    elif (data.startswith(ARCHIVE_MAGIC)
          or data[257:262] == b'ustar'
          or path.lower().endswith(('.tar', '.gz', '.bz2', '.xz', '.7z', '.rar'))):
        raise InspectionBlocked('Unsupported archive format')
    if scanner is None:
        raise InspectionBlocked('Malware policy requires an available scanner')
    receipt = scanner.scan(data)
    if not isinstance(receipt, dict) or receipt.get('verdict') != 'clear' or receipt.get('sha256') != hashlib.sha256(data).hexdigest():
        raise InspectionBlocked('Malformed or mismatched malware receipt')
    return {'policy': 'bounded-clamd-v1', 'scan': receipt}
