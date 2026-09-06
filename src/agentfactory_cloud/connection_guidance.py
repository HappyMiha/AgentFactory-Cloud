"""Read-only projection of accepted Core guidance, never connection authority."""
from datetime import datetime, timezone
from agent_factory.provider_connection_catalog import connection_catalog
from agent_factory.connector_eligibility import catalog_snapshot, setup_decision

# These map product choices to Core informational route IDs, not qualifications.
ELIGIBILITY = {'chatgpt':'codex', 'codex-cli':'codex', 'openai-api':'openai-api',
               'claude-chat':'claude', 'claude-code':'claude', 'anthropic-api':'anthropic-api'}

def guidance(*, actor, workspace, now=None):
    instant = now or datetime.now(timezone.utc)
    catalog = connection_catalog(now=instant)
    terms = catalog_snapshot(at=instant)
    current = bool(catalog['current'] and terms['current'])
    routes = {row['id']: row for row in terms['connectors']}
    products = []
    if current:
        for product in catalog['products']:
            route = routes.get(ELIGIBILITY.get(product['id']))
            # No host approval is installed in this guidance-only consumer.
            gate = setup_decision(product['provider'], None, actor=actor, workspace=workspace, at=instant)
            products.append({'id':product['id'], 'title':product['title'],
                'explanation':product['explanation'], 'flow':product['flow'],
                'sources':product['sources'], 'requirements':route['requirements'] if route else None,
                'privacy':route['privacy'] if route else None,
                'terms_sources':route['sources'] if route else [], 'setup_reason':gate['reason'],
                'can_connect':False, 'execution_ready':False})
    return {'current':current, 'version':catalog['version'], 'terms_revision':terms['revision'],
            'reviewed_on':catalog['reviewed_on'], 'review_due':min(catalog['review_due'],terms['review_due']),
            'products':products, 'connection_checks':catalog['connection_checks'],
            'can_connect':False, 'execution_ready':False, 'qualified_capabilities':[],
            'notice':'Оберіть свій спосіб доступу. Тут можна прочитати пояснення; підключення та перевірка моделей ще недоступні.' if current else
                     'Строк огляду інструкцій минув. Способи підключення приховано до оновлення перевірених джерел.'}
