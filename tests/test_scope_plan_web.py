"""HTTP scope agreement boundaries with actual Core intake and SQLite."""
import test_game_brief_web as brief_api_fixture


class ScopeAPITests(brief_api_fixture.BriefAPITests):
    def plan(self):
        brief = self.create(); url = '/api/briefs/' + brief['id'] + '/scope'
        result = self.client.post(url, json={'command_id': 'scope-0001', 'expected_brief_revision': 1})
        self.assertEqual(result.status_code, 200, result.text)
        return brief, result.json(), url

    def test_scope_route_has_no_client_execution_authority(self):
        brief, plan, url = self.plan()
        self.assertEqual(self.client.get(url).json()['plan']['id'], plan['id'])
        body = {'command_id': 'agree-0001', 'expected_brief_revision': 1, 'expected_plan_revision': 1, 'confirmed': True}
        for field, value in [('confirmed', 'true'), ('approved_by', 'Other'), ('provider', 'remote')]:
            response = self.client.post(url+'/'+plan['id']+'/agree', json=body | {field: value})
            self.assertEqual(response.status_code, 422, response.text)
        response = self.client.post(url+'/'+plan['id']+'/agree', json=body)
        self.assertEqual(response.status_code, 200); self.assertFalse(response.json()['execution_ready'])
        self.assertEqual(self.client.get(url+'/'+plan['id']+'?revision=1').json()['state'], 'draft')

    def test_scope_stale_save_returns_409_and_keeps_latest(self):
        brief, plan, url = self.plan()
        body = {'command_id':'scope-edit-1','expected_brief_revision':1,'expected_plan_revision':1,'scope':plan['scope']}
        self.assertEqual(self.client.post(url+'/'+plan['id']+'/edit',json=body).status_code,200)
        self.assertEqual(self.client.post(url+'/'+plan['id']+'/edit',json=body|{'command_id':'scope-edit-2'}).status_code,409)

    def test_scope_rejects_reading_plan_through_wrong_brief(self):
        brief, plan, url = self.plan()
        self.assertEqual(self.client.get('/api/briefs/other/scope/'+plan['id']).status_code,404)


if __name__ == '__main__':
    import unittest
    unittest.main()
