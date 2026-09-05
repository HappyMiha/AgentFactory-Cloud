"""Consumer conformance counterexamples, never real engine qualification."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('engine_contract',Path(__file__).resolve().parents[1]/'scripts/validate_engine_target_pack.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


class EngineTargetPackTests(unittest.TestCase):
    def setUp(self):
        self.c,self.f=g.load()
        self.request=deepcopy(self.f['request']);self.manifest=deepcopy(self.f['manifest']);self.engine=deepcopy(self.f['engines'][0])

    def plan(self):
        return g.plan(self.request,self.manifest,self.engine,self.c)

    def result(self, operation='probe'):
        self.request['binding']['operation']=operation
        return {'contract_version':self.c['contract_version'],'binding':deepcopy(self.request['binding']),
                'status':'succeeded','mode':self.request['mode'],'payload':deepcopy(self.f['payloads'][operation]),
                'reason':None,'next_action':None,'evidence_ref':'synthetic:proof'}

    def test_two_engine_examples_use_same_nine_operation_contract(self):
        self.assertEqual(g.run_fixtures(self.c,self.f),18)
        self.assertEqual(set(self.c['operations']),{'probe','create','import','validate','test','build','run','collect_crash','export_source'})

    def test_dispatch_does_not_depend_on_an_engine_name(self):
        self.engine['id']='third-unrecognized-engine';self.manifest['engine_id']=self.engine['id'];self.request['binding']['engine_id']=self.engine['id']
        self.assertEqual(self.plan()['status'],'compatible_simulation')
        self.assertEqual(self.plan()['dispatch']['operation'],'probe')

    def test_missing_or_unsupported_operation_is_explicitly_blocked(self):
        for op in ['unknown','run']:
            with self.subTest(operation=op):
                self.request['binding']['operation']=op;self.engine['operations'].remove('run') if 'run' in self.engine['operations'] else None
                result=self.plan();self.assertEqual(result['reason'],'unsupported_operation');self.assertIsNone(result['dispatch']);self.assertTrue(result['next_action'])

    def test_live_never_qualifies_from_a_manifest_or_fixture_flag(self):
        self.request['mode']='live';self.engine['qualification']='qualified';self.request['gates']=['everything_approved']
        self.assertEqual(self.plan()['reason'],'live_qualification_unavailable')

    def test_all_pinned_identity_changes_block(self):
        for key in ['engine_id','engine_version','engine_sha256','target_id','target_version','pack_id','pack_version','pack_sha256']:
            with self.subTest(key=key):
                original=self.request['binding'][key]
                self.request['binding'][key]='f'*64 if key.endswith('sha256') else '2.0.0' if key.endswith('version') else 'changed'
                self.assertEqual(self.plan()['reason'],'incompatible_identity');self.request['binding'][key]=original

    def test_engine_and_pack_versions_must_agree(self):
        self.manifest['engine_version']='2.0.0'
        self.assertEqual(self.plan()['reason'],'incompatible_identity')

    def test_unsupported_target_is_blocked(self):
        self.manifest['target_id']='android';self.request['binding']['target_id']='android'
        self.assertEqual(self.plan()['reason'],'unsupported_target')

    def test_partner_and_store_gates_are_separate(self):
        for target in ['ios','store_package','console_partner']:
            with self.subTest(target=target):
                self.manifest['target_id']=target;self.request['binding']['target_id']=target;self.engine['targets']=[target];self.request['gates']=[]
                self.assertEqual(self.plan()['reason'],'target_gate_required')
                self.request['gates']=self.c['targets'][target].copy()
                self.assertEqual(self.plan()['status'],'compatible_simulation')
                self.request['mode']='live';self.assertEqual(self.plan()['reason'],'live_qualification_unavailable');self.request['mode']='simulation'

    def test_operation_permissions_do_not_expand(self):
        self.request['permissions']=['workspace_read'];self.request['binding']['operation']='create'
        self.assertEqual(self.plan()['reason'],'permission_required')
        self.request['binding']['operation']='probe';self.assertEqual(self.plan()['status'],'compatible_simulation')

    def test_cancellation_cannot_dispatch_or_create_success(self):
        self.request['cancelled']=True
        self.assertEqual(self.plan()['status'],'cancelled');self.assertIsNone(self.plan()['dispatch'])
        with self.assertRaisesRegex(ValueError,'Cancelled'):g.validate_result(self.result(),self.request,self.c)

    def test_non_success_has_no_success_payload(self):
        for status in ['blocked','failed','cancelled']:
            with self.subTest(status=status):
                result=self.result();result.update(status=status,reason='fixture_failure',next_action='Review synthetic failure')
                with self.assertRaises(ValueError):g.validate_result(result,self.request,self.c)
                result['payload']=None;g.validate_result(result,self.request,self.c)
                result['next_action']='';
                with self.assertRaises(ValueError):g.validate_result(result,self.request,self.c)

    def test_replayed_result_cannot_bind_a_different_attempt_or_operation(self):
        for key,value in [('run_attempt',2),('operation_id','another'),('source_sha256','f'*64),('tenant_id','another')]:
            with self.subTest(key=key):
                result=self.result();result['binding'][key]=value
                with self.assertRaisesRegex(ValueError,'mismatch'):g.validate_result(result,self.request,self.c)

    def test_every_operation_payload_is_typed(self):
        for operation in self.c['operations']:
            with self.subTest(operation=operation):
                result=self.result(operation);key=next(iter(result['payload']));result['payload'][key]=None
                with self.assertRaisesRegex(ValueError,'type'):g.validate_result(result,self.request,self.c)

    def test_failed_checks_and_unredacted_crashes_cannot_succeed(self):
        for operation,key,value in [('probe','workspace_ready',False),('validate','errors',1),('test','failed',1),('collect_crash','redacted',False)]:
            with self.subTest(operation=operation):
                result=self.result(operation);result['payload'][key]=value
                with self.assertRaisesRegex(ValueError,'cannot be reported'):g.validate_result(result,self.request,self.c)

    def test_simulation_result_cannot_be_promoted_to_live(self):
        result=self.result();result['mode']='live'
        with self.assertRaisesRegex(ValueError,'mode mismatch'):g.validate_result(result,self.request,self.c)

    def test_versions_digests_and_complete_manifests_are_required(self):
        for key,value in [('contract_version','2.0.0'),('version','latest'),('sha256','unknown'),('operations',[]),('rights_ref','')]:
            with self.subTest(key=key):
                manifest=deepcopy(self.manifest);manifest[key]=value
                with self.assertRaises(ValueError):g.validate_manifest(manifest,self.c)
        del self.manifest['language']
        with self.assertRaises(ValueError):self.plan()

    def test_explicit_limits_reject_booleans_and_unbounded_execution(self):
        for key,value in [('timeout_seconds',0),('output_bytes',-1),('budget_minor',True)]:
            with self.subTest(key=key):
                request=deepcopy(self.request);request['limits'][key]=value
                with self.assertRaises(ValueError):g.validate_request(request,self.c)
        del self.request['limits']['budget_minor']
        with self.assertRaises(ValueError):self.plan()

    def test_input_is_not_mutated(self):
        before=deepcopy((self.request,self.manifest,self.engine));self.plan()
        self.assertEqual((self.request,self.manifest,self.engine),before)


    def test_runtime_requires_the_exact_built_artifact(self):
        result=self.result('run');result['payload']['artifact_sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'Runtime artifact'):g.validate_result(result,self.request,self.c)
        self.request['binding'].update(build_id=None,artifact_sha256=None)
        with self.assertRaisesRegex(ValueError,'built artifact'):self.plan()
        self.request['binding']['operation']='create'
        self.assertEqual(self.plan()['status'],'compatible_simulation')

    def test_result_binding_types_and_toolchain_are_not_coerced(self):
        result=self.result();result['binding']['run_attempt']=True
        with self.assertRaises(ValueError):g.validate_result(result,self.request,self.c)
        result=self.result();result['binding']['toolchain_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'mismatch'):g.validate_result(result,self.request,self.c)


if __name__=='__main__':unittest.main()
