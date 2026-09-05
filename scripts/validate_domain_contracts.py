"""Validate v1 design fixtures. This is not a server or an authorization service."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def load_contracts(root=ROOT):
    folder = root / "contracts" / "v1"
    return tuple(json.loads((folder / name).read_text(encoding="utf-8"))
                 for name in ("domain.json", "transitions.json", "scenarios.json"))


def instant(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return result


def validate_value(value, spec, domain):
    if value is None:
        return spec.get("nullable", False)
    kind = spec["type"]
    if kind == "string":
        valid = isinstance(value, str) and bool(value.strip())
    elif kind in ("positive_integer", "nonnegative_integer"):
        valid = type(value) is int and value >= (1 if kind == "positive_integer" else 0)
    elif kind == "boolean":
        valid = type(value) is bool
    elif kind == "sha256":
        valid = isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))
    elif kind == "timestamp":
        try:
            instant(value)
            valid = True
        except (TypeError, ValueError, AttributeError):
            valid = False
    elif kind in ("string_list", "object_list", "provenance_list"):
        item_type = {"string_list": "string", "object_list": "object",
                     "provenance_list": "provenance"}[kind]
        valid = isinstance(value, list) and all(
            validate_value(item, {"type": item_type}, domain) for item in value)
    elif kind == "object":
        valid = isinstance(value, dict)
    elif kind == "provenance":
        valid = (isinstance(value, dict)
                 and all(key in value for key in domain["provenance_fields"])
                 and value.get("rights_status") in domain["rights_states"]
                 and all(isinstance(value.get(key), str) and value[key].strip()
                         for key in ("asserted_owner", "origin", "license_version"))
                 and isinstance(value.get("attribution"), str)
                 and all(validate_value(value.get(key), {"type": "string_list"}, domain)
                         for key in ("allowed_uses", "evidence_refs")))
    else:
        raise ValueError(f"Unknown field type: {kind}")
    return valid and ("enum" not in spec or value in spec["enum"])


def validate_records(records, domain):
    """Check typed records and internal tenant references; return all errors."""
    errors = []
    index = {(r.get("entity"), r.get("id")): r for r in records}
    if len(index) != len(records):
        errors.append("duplicate entity/id")
    for record in records:
        label = f"{record.get('entity')}:{record.get('id')}"
        definition = domain["entities"].get(record.get("entity"))
        if definition is None:
            errors.append(f"{label}: unknown entity")
            continue
        if record.get("state") not in definition["states"]:
            errors.append(f"{label}: invalid state")
        fields = {**domain["common_fields"], **definition["fields"]}
        if set(record) - set(fields) - {"entity"}:
            errors.append(f"{label}: unknown fields")
        for name, spec in fields.items():
            if name not in record or not validate_value(record[name], spec, domain):
                errors.append(f"{label}: invalid {name}")
                continue
            if "reference" in spec and record[name] is not None:
                target = index.get((spec["reference"], record[name]))
                if target is None or target.get("tenant_id") != record.get("tenant_id"):
                    errors.append(f"{label}: invalid tenant reference {name}")
        tenant = index.get(("Tenant", record.get("tenant_id")))
        if tenant is None:
            errors.append(f"{label}: missing tenant")
        for name in ("source_version_id", "build_id", "run_id", "play_session_id"):
            if name in record and name in fields:
                target = index.get((fields[name]["reference"], record[name]))
                if target and target.get("project_id") != record.get("project_id"):
                    errors.append(f"{label}: cross-project {name}")
        if record.get("entity") == "Purchase":
            offer = record.get("offer_snapshot", {})
            required = ("seller_tenant_id", "listing_id", "listing_revision",
                        "release_public_ref", "license_version", "offer_token",
                        "price_minor", "currency")
            if (not isinstance(offer, dict) or any(key not in offer for key in required)
                    or not validate_value(offer.get("listing_revision"), {"type": "positive_integer"}, domain)
                    or not validate_value(offer.get("price_minor"), {"type": "nonnegative_integer"}, domain)
                    or any(not validate_value(offer.get(key), {"type": "string"}, domain)
                           for key in required if key not in ("listing_revision", "price_minor"))
                    or offer.get("price_minor") != record.get("price_minor")
                    or offer.get("currency") != record.get("currency")):
                errors.append(f"{label}: invalid offer snapshot")
        if record.get("entity") == "Entitlement":
            purchase = index.get(("Purchase", record.get("purchase_id")))
            if purchase:
                offer = purchase.get("offer_snapshot")
                if (not isinstance(offer, dict)
                        or record.get("user_id") != purchase.get("buyer_user_id")
                        or record.get("release_public_ref") != offer.get("release_public_ref")
                        or record.get("license_version") != offer.get("license_version")):
                    errors.append(f"{label}: entitlement does not match purchase")
                if record.get("state") == "active" and purchase.get("state") != "paid":
                    errors.append(f"{label}: active entitlement requires paid purchase")
    return errors


class Denied(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


class ReferenceModel:
    """In-memory state-command example with injected, trusted identity and time.

    Receipts, identities and evidence are fixtures, not production trust roots.
    Create/read/edit/payment adapters must implement the accompanying API design.
    """

    def __init__(self, domain, transitions, records, now):
        errors = validate_records(records, domain)
        if errors:
            raise ValueError("; ".join(errors))
        self.domain, self.transitions = domain, transitions
        self.records = {(r["entity"], r["id"]): deepcopy(r) for r in records}
        self.now = instant(now)
        self.receipts = {}

    def get(self, entity, ident, tenant):
        record = self.records.get((entity, ident))
        if not record or record["tenant_id"] != tenant or record["deleted"]:
            raise Denied(404, "resource_not_found")
        if "project_id" in record:
            self.get("Project", record["project_id"], tenant)
        return record

    def linked(self, record, entity, field):
        return self.get(entity, record[field], record["tenant_id"])

    def binding(self, record):
        entity = record["entity"]
        if entity == "Run":
            source = self.linked(record, "SourceVersion", "source_version_id")
            blueprint = self.linked(record, "FactoryBlueprint", "blueprint_id")
            return {"source_version_id": source["id"], "source_sha256": source["content_sha256"],
                    "blueprint_id": blueprint["id"], "blueprint_sha256": blueprint["content_sha256"],
                    "workspace_ref": record["workspace_ref"], "model_profile": record["model_profile"],
                    "attempt": record["attempt"]}
        if entity == "Listing":
            return {key: record[key] for key in ("id", "release_id", "price_minor", "currency")} | {
                "license_version": record["provenance"]["license_version"]}
        build = record if entity == "Build" else self.linked(record, "Build", "build_id")
        source = self.linked(build, "SourceVersion", "source_version_id")
        run = self.linked(build, "Run", "run_id")
        result = {"build_id": build["id"], "source_version_id": source["id"],
                  "source_sha256": source["content_sha256"], "artifact_sha256": build["artifact_sha256"],
                  "target_profile": build["target_profile"], "run_id": run["id"], "attempt": run["attempt"]}
        if entity == "Release":
            result["release_id"] = record["id"]
        return result

    def proof(self, proof, binding):
        try:
            valid = (isinstance(proof, dict) and proof["status"] == "passed"
                     and proof["mode"] == "live" and proof["binding"] == binding
                     and bool(proof["evidence_ref"])
                     and instant(proof["checked_at"]) <= self.now < instant(proof["expires_at"]))
        except (KeyError, TypeError, ValueError, AttributeError):
            valid = False
        if not valid:
            raise Denied(409, "evidence_not_current")

    def check_set(self, record, group):
        checks = record["checks"]
        for name in self.transitions["required_checks"][group]:
            matching = [c for c in checks if c.get("name") == name]
            if len(matching) != 1:
                raise Denied(409, "evidence_missing_or_duplicate")
            self.proof(matching[0], self.binding(record))

    def readiness(self, run):
        source = self.linked(run, "SourceVersion", "source_version_id")
        blueprint = self.linked(run, "FactoryBlueprint", "blueprint_id")
        brief = self.linked(blueprint, "GameBrief", "brief_id")
        team = self.linked(run, "AgentTeam", "team_id")
        if (source["state"] != "available" or blueprint["state"] != "approved"
                or brief["state"] != "approved" or team["state"] != "active"
                or team["blueprint_id"] != blueprint["id"] or brief["project_id"] != run["project_id"]):
            raise Denied(409, "inputs_not_ready")
        self.check_set(run, "readiness")

    def build_evidence(self, build):
        run = self.linked(build, "Run", "run_id")
        source = self.linked(build, "SourceVersion", "source_version_id")
        blueprint = self.linked(run, "FactoryBlueprint", "blueprint_id")
        if (run["state"] != "succeeded" or source["state"] != "available"
                or run["source_version_id"] != source["id"]
                or build["target_profile"] != blueprint["target_profile"]):
            raise Denied(409, "inputs_not_ready")
        self.check_set(build, "build_evidence")

    def release_evidence(self, release):
        build = self.linked(release, "Build", "build_id")
        if build["state"] != "ready" or release["source_version_id"] != build["source_version_id"]:
            raise Denied(409, "inputs_not_ready")
        self.build_evidence(build)

    def rights(self, record):
        requested = "build" if record["entity"] == "Build" else "publish"
        provenance = []
        if record["entity"] == "Listing":
            requested = "sell" if record["price_minor"] > 0 else "publish"
            provenance.append(record["provenance"])
            record = self.linked(record, "Release", "release_id")
        build = record if record["entity"] == "Build" else self.linked(record, "Build", "build_id")
        source = self.linked(build, "SourceVersion", "source_version_id")
        provenance += [build["provenance"], source["provenance"], *source["asset_provenance"]]
        for item in provenance:
            if (item["rights_status"] != "verified" or requested not in item["allowed_uses"]
                    or not item["evidence_refs"]):
                raise Denied(409, "rights_not_cleared")

    def guard(self, name, record):
        if name == "execution":
            self.check_set(record, "execution")
        elif name in ("readiness", "build_evidence", "release_evidence", "rights"):
            getattr(self, name)(record)
        elif name == "approval":
            self.proof(record["approval"], self.binding(record))
        elif name == "moderation":
            self.proof(record["moderation"], self.binding(record))
        elif name == "release_approved":
            release = self.linked(record, "Release", "release_id")
            if release["state"] != "approved":
                raise Denied(409, "release_not_approved")
            self.release_evidence(release)
            self.proof(release["approval"], self.binding(release))
        elif name == "no_public_listing":
            for item in self.records.values():
                if item["entity"] == "Listing" and item["tenant_id"] == record["tenant_id"] and item["state"] == "published":
                    release = self.linked(item, "Release", "release_id")
                    if release["project_id"] == record["id"]:
                        raise Denied(409, "publication_exists")
        else:
            raise ValueError(f"Unimplemented guard: {name}")

    def execute(self, request, actor):
        """Return a response, changing records only after every guard passes."""
        try:
            if not actor or not actor.get("authenticated") or instant(actor["expires_at"]) <= self.now:
                raise Denied(401, "authentication_required")
            tenant = request["tenant_id"]
            if tenant not in actor.get("tenant_ids", []):
                raise Denied(404, "resource_not_found")
            account = self.get("Tenant", tenant, tenant)
            if account["state"] != "active":
                raise Denied(403, "tenant_inactive")
            operation = self.transitions["operations"].get(request["operation"])
            if not operation:
                raise Denied(400, "unknown_operation")
            if operation["scope"] not in actor.get("scopes", []):
                raise Denied(403, "permission_denied")
            key = request.get("idempotency_key")
            if not isinstance(key, str) or not key.strip() or len(key) > 128:
                raise Denied(400, "idempotency_key_required")
            receipt_key = (tenant, actor["id"], request["operation"], request["resource_id"], key)
            fingerprint = hashlib.sha256(json.dumps(
                {"body": request.get("body", {}), "if_match": request.get("if_match")},
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            receipt = self.receipts.get(receipt_key)
            if receipt:
                if receipt["fingerprint"] != fingerprint:
                    raise Denied(409, "idempotency_conflict")
                if self.now >= receipt["expires_at"]:
                    raise Denied(409, "idempotency_expired")
                return deepcopy(receipt["response"])
            record = self.get(operation["entity"], request["resource_id"], tenant)
            if request.get("if_match") is None:
                raise Denied(428, "precondition_required")
            if request["if_match"] != f'"r{record["revision"]}"':
                raise Denied(412, "revision_conflict")
            if request.get("body", {}) != {}:
                raise Denied(422, "unexpected_command_fields")
            if record["state"] not in operation["from"]:
                raise Denied(409, "invalid_transition")
            for guard in operation["guards"]:
                self.guard(guard, record)
            updated = deepcopy(record)
            updated.update(state=operation["to"], revision=record["revision"] + 1,
                           updated_at=self.now.isoformat())
            if operation.get("invalidate_checks"):
                updated["attempt"] += 1
                updated["checks"] = []
            if operation.get("delete"):
                updated["deleted"] = True
            response = {"status": 204 if updated["deleted"] else 200,
                        "code": "ok", "etag": f'"r{updated["revision"]}"'}
            if not updated["deleted"]:
                response["record"] = deepcopy(updated)
            self.records[(updated["entity"], updated["id"])] = updated
            self.receipts[receipt_key] = {
                "fingerprint": fingerprint, "response": deepcopy(response),
                "expires_at": self.now + timedelta(hours=self.domain["mutation_rules"]["receipt_retention_hours"])}
            return response
        except Denied as error:
            return {"status": error.status, "code": error.code}


def run_scenarios(domain, transitions, fixtures):
    count = 0
    for scenario in fixtures["scenarios"]:
        records = deepcopy(fixtures["records"])
        for patch in scenario.get("record_patches", []):
            record = next(r for r in records if r["entity"] == patch["entity"] and r["id"] == patch["id"])
            record.update(patch)
        model = ReferenceModel(domain, transitions, records, fixtures["now"])
        actor = deepcopy(fixtures["actor"])
        actor.update(scenario.get("actor_patch", {}))
        for request in scenario["requests"]:
            response = model.execute(request, actor)
            expected = request["expected"]
            for key, value in expected.items():
                if response.get(key) != value:
                    raise ValueError(f'{scenario["name"]}: {key}: {response.get(key)!r} != {value!r}')
            count += 1
    return count


def main():
    domain, transitions, fixtures = load_contracts()
    if domain["contract_version"] != transitions["contract_version"] or domain["contract_version"] != fixtures["contract_version"]:
        raise ValueError("Contract versions differ")
    for operation in transitions["operations"].values():
        states = domain["entities"][operation["entity"]]["states"]
        if any(state not in states for state in [*operation["from"], operation["to"]]):
            raise ValueError("Transition names an unknown state")
    count = run_scenarios(domain, transitions, fixtures)
    print(f'Validated {len(domain["entities"])} entity definitions and {count} scenario requests; design fixtures only.')


if __name__ == "__main__":
    main()
