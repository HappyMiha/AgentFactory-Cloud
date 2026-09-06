"""Server-resolved tenant policy. Client role/tenant claims never grant authority."""
from dataclasses import dataclass, field

ROLES = frozenset({'Creator', 'Player', 'Moderator', 'Support', 'Admin'})
ACTIONS = frozenset({'read', 'write', 'play', 'moderate', 'support_read'})
KINDS = frozenset({'project', 'artifact', 'worker_result', 'preview', 'build', 'moderation', 'support'})


class AccessDenied(Exception):
    def __init__(self, code='not_found', status=404):
        self.code, self.status = code, status
        super().__init__(code)


@dataclass(frozen=True)
class Principal:
    account_id: str
    session_key: str = field(repr=False)
    generation: int


@dataclass(frozen=True)
class Resource:
    tenant_id: str
    owner_id: str
    kind: str
    visibility: str = 'private'
    redacted: bool = False
    # Current server-side support ticket authorization, not caller JSON.
    support_accounts: frozenset[str] = frozenset()


def permits(roles, account_id, action, resource):
    if (action not in ACTIONS or resource.kind not in KINDS
            or resource.visibility not in {'private', 'public'}):
        return False
    if 'Admin' in roles:
        if resource.kind == 'support':
            return action == 'support_read' and resource.redacted is True
        return action != 'support_read'
    if ('Creator' in roles and account_id == resource.owner_id
            and resource.kind in {'project', 'artifact', 'worker_result', 'preview', 'build'}
            and action in {'read', 'write', 'play'}):
        return True
    if ('Player' in roles and resource.kind in {'build', 'preview'}
            and resource.visibility == 'public' and action in {'read', 'play'}):
        return True
    if 'Moderator' in roles and resource.kind == 'moderation' and action in {'read', 'moderate'}:
        return resource.redacted is True
    if 'Support' in roles and resource.kind == 'support' and action == 'support_read':
        return resource.redacted is True and account_id in resource.support_accounts
    return False
