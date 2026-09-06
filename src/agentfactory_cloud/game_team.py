"""A visible role proposal and Core-owned gap assessment, never a live team."""
from contextlib import closing
from dataclasses import asdict
import hashlib
import json
from agent_factory.roles import ContractField, RoleDefinition, RoleRegistry
from agent_factory.storage import SQLiteStorage
from agent_factory.workforce import RolePoolRequirement, WorkforceComposer
from .game_briefs import BriefConflict
from .scope_plans import ScopePlans

PACK_VERSION = "1.0.0"
ROLES = (
    ("game-director", "Game Director", "Keep the agreed game goal, coordinate work and explain blockers.", 15),
    ("game-designer", "Designer", "Turn the agreed goal into clear rules and player interactions.", 20),
    ("game-developer", "Developer", "Implement the approved game changes and report what changed.", 35),
    ("game-qa", "QA / Playtester", "Check the actual game against its rules and report failures independently.", 20),
    ("game-build", "Build Engineer", "Produce the game package and verify the exact delivered files.", 10),
)


def role_pack():
    return tuple(RoleDefinition(
        id=key, version=PACK_VERSION, purpose=description, responsibilities=(description,),
        inputs=(ContractField("accepted_scope", "object"), ContractField("source_revision", "string")),
        outputs=(ContractField("result", "object"),), tools=(), permissions=("read_project",),
        limits=(("max_parallel", 1.0),),
        evidence=(ContractField("artifact_digest", "string"), ContractField("effective_identity", "string")),
        incompatible_duties=(("game-qa",) if key == "game-developer" else ("game-developer",) if key == "game-qa" else ()),
    ) for key, title, description, share in ROLES)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",", ":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


class GameTeams:
    def __init__(self, briefs):
        self.briefs=briefs
        self.plans=ScopePlans(briefs)

    def _snapshot(self, ident, actor):
        brief=self.briefs.get(ident,actor)
        plan=self.plans.latest(ident,actor)
        binding={"actor":actor,"brief_id":ident,"brief_revision":brief["revision"],
                 "source_sha256":brief["source_sha256"], "mission_id":brief["core_mission_id"],
                 "plan_id":plan["id"] if plan else None,"plan_revision":plan["revision"] if plan else None,
                 "plan_digest":digest(plan) if plan else None,"pack_digest":digest([asdict(r) for r in role_pack()])}
        return brief,plan,binding,digest(binding)

    def _view(self, ident, actor):
        brief,plan,binding,stamp=self._snapshot(ident,actor)
        allowance=plan["scope"]["token_allowance"] if plan else 0
        shares=[allowance*role[3]//100 for role in ROLES]
        shares[0]+=allowance-sum(shares)
        prepared=None
        if self.briefs.core_database.exists():
            with closing(SQLiteStorage(self.briefs.core_database)) as core:
                row=core.db.execute("SELECT id,status,composition_digest FROM workforce_compositions WHERE composition_key=?",("cloud-game-team:"+stamp,)).fetchone()
                if row:prepared=dict(row)
        return {"brief_id":ident,"brief_revision":brief["revision"],"source_sha256":brief["source_sha256"],
                "plan_id":binding["plan_id"],"plan_revision":binding["plan_revision"],"snapshot_digest":stamp,
                "pack_version":PACK_VERSION,"core_assessment":prepared,
                "can_assess":bool(plan and not plan["stale"] and plan["state"]=="scope_agreed"),
                "state":"waiting_for_verified_connections", "execution_ready":False,"can_start":False,"can_stop":False,
                "planned_tokens":allowance,"approved_spend":0,"recorded_spend":None,
                "budget_note":"Token shares are planning allowances, not reservations, measured usage or permission to spend.",
                "notice":"No AI team is running here. Current account access and two independently verified coding/checking routes are still required. You can inspect the roles and prepare a gap assessment without starting AI.",
                "roles":[{"id":key,"title":title,"responsibility":purpose,"planned_tokens":shares[i],
                          "status":"unassigned","effective_model":None,"current_work":None} for i,(key,title,purpose,share) in enumerate(ROLES)]}

    def view(self, ident, actor):
        # Keep the displayed brief/scope binding coherent with concurrent edits.
        with closing(self.briefs.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            return self._view(ident,actor)

    def assess(self, ident, actor, expected_digest):
        if not isinstance(expected_digest,str) or len(expected_digest)!=64:
            raise ValueError("Reload the saved plan before preparing the team.")
        with closing(self.briefs.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            brief,plan,binding,stamp=self._snapshot(ident,actor)
            if stamp!=expected_digest or not plan or plan["stale"] or plan["state"]!="scope_agreed":
                raise BriefConflict("The saved scope changed or has not been agreed. Review it before preparing the team.")
            with self.briefs.core_lock, closing(SQLiteStorage(self.briefs.core_database)) as core:
                registry=RoleRegistry(core)
                for role in role_pack():registry.register(role)
                # Empty pools are deliberate. Do not accept caller-provided scopes,
                # workers, model brands or legacy qualifications as live authority.
                pools=tuple(RolePoolRequirement(key=key,role_id=key,role_version=PACK_VERSION,
                    qualification_role=title,required_capabilities=("independent_review",) if key=="game-qa" else ("cloud_coding",),
                    pool_strategy="singleton",routing_strategy="cost-aware",minimum_replicas=1,maximum_replicas=1,
                    arbitration_rule="single",candidates=()) for key,title,_,_ in ROLES)
                result=WorkforceComposer(core).compose(composition_key="cloud-game-team:"+stamp,
                    mission_key="cloud-brief:"+digest(binding),pools=pools,budget=0)
                if result.status=="ready":raise RuntimeError("An empty game team cannot be ready")
            return self._view(ident,actor)
