"""Negative contract cases: these test the reference model, not a Cloud server."""
from copy import deepcopy
from datetime import timedelta
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "domain_contracts", Path(__file__).resolve().parents[1] / "scripts/validate_domain_contracts.py")
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


class DomainContractsTest(unittest.TestCase):
    def setUp(self):
        self.domain, self.transitions, self.fixtures = contract.load_contracts()
        self.model = contract.ReferenceModel(self.domain, self.transitions,
                                             self.fixtures["records"], self.fixtures["now"])
        self.actor = deepcopy(self.fixtures["actor"])

    def record(self, entity, ident=None):
        return next(r for r in self.model.records.values()
                    if r["entity"] == entity and (ident is None or r["id"] == ident))

    def request(self, operation="run.start", ident="run_a", **changes):
        return dict(operation=operation, resource_id=ident, tenant_id="tenant_a",
                    if_match='"r1"', idempotency_key="test-key", body={}) | changes

    def assert_denied(self, request, code, status=409):
        before = deepcopy(self.model.records)
        receipts = deepcopy(self.model.receipts)
        response = self.model.execute(request, self.actor)
        self.assertEqual(response, {"status": status, "code": code})
        self.assertEqual(self.model.records, before)
        self.assertEqual(self.model.receipts, receipts)

    def test_all_documented_scenarios(self):
        self.assertEqual(contract.run_scenarios(self.domain, self.transitions, self.fixtures), 26)

    def test_all_entities_have_valid_baseline_examples(self):
        self.assertEqual({r["entity"] for r in self.fixtures["records"]}, set(self.domain["entities"]))
        self.assertEqual(contract.validate_records(self.fixtures["records"], self.domain), [])

    def test_missing_required_fields_are_not_defaulted(self):
        for entity, definition in self.domain["entities"].items():
            for field in {**self.domain["common_fields"], **definition["fields"]}:
                with self.subTest(entity=entity, field=field):
                    records = deepcopy(self.fixtures["records"])
                    target = next(r for r in records if r["entity"] == entity)
                    del target[field]
                    self.assertTrue(contract.validate_records(records, self.domain))

    def test_boolean_is_not_revision_or_price(self):
        for entity, field in (("Run", "revision"), ("Listing", "price_minor")):
            with self.subTest(field=field):
                records = deepcopy(self.fixtures["records"])
                next(r for r in records if r["entity"] == entity)[field] = True
                self.assertTrue(contract.validate_records(records, self.domain))

    def test_internal_cross_tenant_reference_is_rejected(self):
        records = deepcopy(self.fixtures["records"])
        tenant = deepcopy(records[0])
        tenant.update(id="tenant_b", tenant_id="tenant_b")
        records.append(tenant)
        next(r for r in records if r["entity"] == "SourceVersion")["tenant_id"] = "tenant_b"
        self.assertTrue(contract.validate_records(records, self.domain))

    def test_cross_project_build_is_rejected(self):
        records = deepcopy(self.fixtures["records"])
        project = deepcopy(next(r for r in records if r["entity"] == "Project"))
        project["id"] = "project_b"
        records.append(project)
        next(r for r in records if r["entity"] == "Build")["project_id"] = "project_b"
        self.assertTrue(contract.validate_records(records, self.domain))

    def test_missing_duplicate_failed_simulated_and_stale_evidence(self):
        base = deepcopy(self.record("Run")["checks"])
        cases = [([], "evidence_missing_or_duplicate"),
                 (base + [deepcopy(base[0])], "evidence_missing_or_duplicate")]
        for field, value in (("status", "failed"), ("mode", "simulation"),
                             ("expires_at", self.fixtures["now"]),
                             ("checked_at", "2026-09-06T12:00:00Z"),
                             ("evidence_ref", ""), ("binding", {})):
            checks = deepcopy(base)
            checks[0][field] = value
            cases.append((checks, "evidence_not_current"))
        for checks, error in cases:
            with self.subTest(checks=checks[:1]):
                self.record("Run")["checks"] = checks
                self.assert_denied(self.request(), error)

    def test_evidence_is_bound_to_every_run_input(self):
        original = deepcopy(self.record("Run")["checks"])
        for field in original[0]["binding"]:
            with self.subTest(field=field):
                changed = deepcopy(original)
                changed[0]["binding"][field] = "different"
                self.record("Run")["checks"] = changed
                self.assert_denied(self.request(), "evidence_not_current")

    def test_build_proof_cannot_move_to_new_artifact(self):
        self.record("Run")["state"] = "succeeded"
        self.record("Build")["artifact_sha256"] = "e" * 64
        self.assert_denied(self.request("build.qualify", "build_a"), "evidence_not_current")

    def test_unknown_asset_rights_block_build(self):
        self.record("Run")["state"] = "succeeded"
        self.record("SourceVersion")["asset_provenance"][0]["rights_status"] = "unknown"
        self.assert_denied(self.request("build.qualify", "build_a"), "rights_not_cleared")

    def test_release_cannot_reuse_approval_for_different_source(self):
        self.record("Run")["state"] = "succeeded"
        self.record("Build")["state"] = "ready"
        self.record("Release")["approval"]["binding"]["source_sha256"] = "e" * 64
        self.assert_denied(self.request("release.approve", "release_a"), "evidence_not_current")

    def prepare_listing(self):
        self.record("Run")["state"] = "succeeded"
        self.record("Build")["state"] = "ready"
        self.record("Release")["state"] = "approved"

    def test_publication_rechecks_build_after_release_approval(self):
        self.prepare_listing()
        self.record("Build")["checks"][0]["status"] = "failed"
        self.assert_denied(self.request("listing.publish", "listing_a"), "evidence_not_current")

    def test_price_change_invalidates_moderation(self):
        self.prepare_listing()
        self.record("Listing")["price_minor"] = 490
        self.assert_denied(self.request("listing.publish", "listing_a"), "evidence_not_current")

    def test_sale_needs_sell_rights_on_every_asset(self):
        self.prepare_listing()
        listing = self.record("Listing")
        listing["price_minor"] = 490
        listing["moderation"]["binding"] = self.model.binding(listing)
        self.record("SourceVersion")["asset_provenance"][0]["allowed_uses"] = ["build", "publish"]
        self.assert_denied(self.request("listing.publish", "listing_a"), "rights_not_cleared")

    def test_exact_retry_replays_without_second_mutation(self):
        first = self.model.execute(self.request(), self.actor)
        self.assertEqual(first["status"], 200)
        second = self.model.execute(self.request(), self.actor)
        self.assertEqual(second, first)
        self.assertEqual(self.record("Run")["revision"], 2)
        second["record"]["state"] = "failed"
        self.assertEqual(self.record("Run")["state"], "running")

    def test_same_key_with_new_precondition_is_conflict(self):
        self.model.execute(self.request(), self.actor)
        self.assert_denied(self.request(if_match='"r2"'), "idempotency_conflict")

    def test_expired_receipt_never_executes_again(self):
        self.model.execute(self.request(), self.actor)
        self.model.now += timedelta(hours=24)
        self.actor["expires_at"] = "2026-09-08T12:00:00Z"
        self.assert_denied(self.request(), "idempotency_expired")

    def test_replay_rechecks_authority(self):
        self.model.execute(self.request(), self.actor)
        self.actor["scopes"] = []
        self.assert_denied(self.request(), "permission_denied", 403)

    def test_other_actor_cannot_replay_receipt(self):
        self.model.execute(self.request(), self.actor)
        self.actor["id"] = "another-authenticated-user"
        self.assert_denied(self.request(), "revision_conflict", 412)

    def test_deleted_project_hides_child_but_delete_replays(self):
        request = self.request("project.delete", "project_a")
        self.assertEqual(self.model.execute(request, self.actor)["status"], 204)
        self.assertEqual(self.model.execute(request, self.actor)["status"], 204)
        self.assert_denied(self.request(), "resource_not_found", 404)

    def test_retry_increments_attempt_and_discards_old_evidence(self):
        self.record("Run")["state"] = "failed"
        response = self.model.execute(self.request("run.retry"), self.actor)
        self.assertEqual(response["record"]["attempt"], 2)
        self.assertEqual(response["record"]["checks"], [])
        self.assert_denied(self.request("run.qualify", if_match='"r2"'), "evidence_missing_or_duplicate")

    def test_success_requires_execution_proof_not_only_readiness(self):
        self.record("Run")["state"] = "running"
        self.record("Run")["checks"] = [p for p in self.record("Run")["checks"] if p["name"] != "execution"]
        self.assert_denied(self.request("run.succeed"), "evidence_missing_or_duplicate")

    def test_purchase_price_must_match_immutable_public_offer(self):
        records = deepcopy(self.fixtures["records"])
        next(r for r in records if r["entity"] == "Purchase")["price_minor"] = 1
        self.assertTrue(contract.validate_records(records, self.domain))

    def test_unknown_fields_do_not_silently_gain_meaning(self):
        records = deepcopy(self.fixtures["records"])
        records[0]["is_admin"] = True
        self.assertTrue(contract.validate_records(records, self.domain))

    def test_active_entitlement_needs_matching_paid_purchase(self):
        for field, value in (("state", "active"), ("release_public_ref", "another-release"),
                             ("license_version", "another-license")):
            with self.subTest(field=field):
                records = deepcopy(self.fixtures["records"])
                next(r for r in records if r["entity"] == "Entitlement")[field] = value
                self.assertTrue(contract.validate_records(records, self.domain))

    def test_offer_fields_are_typed(self):
        for field, value in (("listing_revision", True), ("seller_tenant_id", ""),
                             ("offer_token", None)):
            with self.subTest(field=field):
                records = deepcopy(self.fixtures["records"])
                next(r for r in records if r["entity"] == "Purchase")["offer_snapshot"][field] = value
                self.assertTrue(contract.validate_records(records, self.domain))


if __name__ == "__main__":
    unittest.main()
