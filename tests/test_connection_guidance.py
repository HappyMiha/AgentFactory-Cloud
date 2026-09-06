from datetime import datetime,timezone
from pathlib import Path
import unittest
from unittest.mock import patch
from agent_factory.provider_connection_catalog import connection_catalog
from agentfactory_cloud.connection_guidance import guidance

NOW=datetime(2026,9,6,12,tzinfo=timezone.utc)
class ConnectionGuidanceTests(unittest.TestCase):
    def view(self,at=NOW):return guidance(actor='Creator',workspace=Path('workspace'),now=at)
    def test_projects_core_products_without_setup_or_capability_authority(self):
        v=self.view();core=connection_catalog(now=NOW)
        self.assertEqual([p['id'] for p in v['products']],[p['id'] for p in core['products']])
        for p,c in zip(v['products'],core['products']):
            self.assertEqual(p['explanation'],c['explanation']);self.assertEqual(p['sources'],c['sources'])
            self.assertFalse(p['can_connect']);self.assertFalse(p['execution_ready'])
        self.assertFalse(v['execution_ready']);self.assertFalse(v['can_connect']);self.assertEqual(v['qualified_capabilities'],[])
        self.assertEqual(set(v['connection_checks'].values()),{'not_run'})
        self.assertEqual(next(p for p in v['products'] if p['id']=='openai-api')['setup_reason'],'adult_review_required')
    def test_expired_or_future_catalogue_hides_guidance(self):
        for at in (datetime(2026,10,6,tzinfo=timezone.utc),datetime(2026,9,5,tzinfo=timezone.utc)):
            v=self.view(at);self.assertFalse(v['current']);self.assertEqual(v['products'],[])
    def test_either_catalogue_can_suspend_and_snapshots_are_detached(self):
        from agentfactory_cloud import connection_guidance as module
        original=module.catalog_snapshot
        with patch.object(module,'catalog_snapshot',side_effect=lambda **kw:original(**kw)|{'current':False}):
            self.assertEqual(self.view()['products'],[])
        v=self.view();v['products'][0]['sources'].clear();self.assertTrue(self.view()['products'][0]['sources'])
