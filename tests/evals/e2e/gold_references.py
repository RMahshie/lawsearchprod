"""Gold standard references for e2e eval judging.

Each entry maps a question ID (from questions.py) to a GoldReference
containing the facts the answer must include, errors it must avoid,
and the expected classify/route outputs.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence


FactType = Literal["statutory", "derived", "inference", "absence"]
RuleType = Literal["prohibited_error"]
VerificationStatus = Literal["verified", "needs_review"]


@dataclass(frozen=True)
class SourceEvidence:
    """A durable locator for the corpus evidence supporting a criterion."""

    bill: str
    division: str
    locator: str
    source_file: str = ""
    line_start: int = 0
    line_end: int = 0
    anchor: str = ""
    chunk_id: str | None = None
    excerpt: str | None = None
    source_hash: str | None = None


@dataclass(frozen=True)
class CorpusScope:
    """The bounded corpus against which an absence claim was verified."""

    bills: tuple[str, ...]
    divisions: tuple[str, ...] = ()
    description: str = ""
    source_files: tuple[str, ...] = ()
    complete: bool = False
    search_query: str = ""


@dataclass(frozen=True)
class GoldFact:
    id: str
    statement: str
    weight: int = 1
    fact_type: FactType = "statutory"
    verification_status: VerificationStatus = "verified"
    evidence: tuple[SourceEvidence, ...] = ()
    corpus_scope: CorpusScope | None = None
    equation: str | None = None


@dataclass(frozen=True)
class GoldRule:
    id: str
    statement: str
    weight: int = 1
    fact_type: RuleType = "prohibited_error"
    verification_status: VerificationStatus = "verified"
    evidence: tuple[SourceEvidence, ...] = ()


@dataclass(frozen=True)
class AnswerShapeRule:
    id: str
    statement: str


@dataclass(frozen=True)
class GoldAlternative:
    id: str
    statement: str
    satisfies: tuple[str, ...]


# Descriptive aliases keep the schema discoverable without forcing callers to
# depend on one naming convention.
GoldEvidence = SourceEvidence
GoldError = GoldRule
StructuralRule = AnswerShapeRule


_DIVISION_BILL: dict[str, str] = {
    "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES": "PL37",
    "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES": "PL74",
    "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES": "PL74",
    "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES": "PL74",
    "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES": "PL37",
    "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES": "PL75",
    "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS": "PL37/PL75",
    "FINANCIAL SERVICES AND GENERAL GOVERNMENT": "PL75",
}

_BILL_FILE = {
    "PL37": "data/bills/2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm",
    "PL74": "data/bills/2026/FY2026_CommerceJusticeScience_EnergyWaterDev_INTERIOREnvironmental.htm",
    "PL75": "data/bills/2026/FY2026_CONSOLIDATED.htm",
}

# Full-file hashes make source changes fail benchmark validation and force an
# explicit re-audit instead of silently preserving stale line references.
_BILL_SHA256 = {
    "PL37": "f65bc9332c21a79ff9597044a1832727545d48282e3b5ebbf3f65bf19abf0318",
    "PL74": "363facdf52c87aa6801d56ae5720b096b20da8d2da94dccc21db9229e025abcd",
    "PL75": "183c34fe55c7b8dab2a7c42675c9e8909b7c3a81c64b6990d459c8996d839fdc",
}

# Audit-checked source ranges.  A question may cite more than one bill; each
# criterion receives all ranges relevant to that question so provenance stays
# durable even when a paraphrase does not contain a verbatim quotation.
_QUESTION_SOURCES: dict[str, tuple[tuple[str, int, int, str], ...]] = {
    "direct_1": (("PL37", 2554, 2684, "Salaries and Expenses"),),
    "direct_2": (("PL37", 1342, 1365, "Food Safety and Inspection Service"),),
    "direct_3": (("PL74", 2144, 2165, "Science"),),
    "direct_4": (("PL74", 7297, 7379, "Environmental Programs and Management"),),
    "direct_5": (("PL37", 6511, 6537, "Medical Services"), ("PL37", 7601, 7622, "medical services")),
    "broad_1": (("PL37", 2077, 2153, "Rural Water"), ("PL74", 4187, 4199, "Northwestern New Mexico"), ("PL74", 7466, 7819, "State and Tribal Assistance Grants")),
    "broad_2": (("PL75", 12388, 13664, "Housing"),),
    "broad_3": (("PL75", 9624, 9754, "Airport"),),
    "broad_4": (("PL74", 1444, 1912, "Office of Justice Programs"),),
    "broad_5": (("PL74", 7297, 7901, "Superfund"), ("PL74", 8762, 8766, "Health Sciences")),
    "mechanism_1": (("PL37", 105, 222, "continuing appropriations"), ("PL75", 27241, 27277, "February 13, 2026")),
    "mechanism_2": (("PL37", 105, 174, "Continuing Appropriations Act"), ("PL75", 27241, 27277, "February 13, 2026")),
    "mechanism_3": (("PL37", 114, 127, "rate for operations"), ("PL37", 246, 250, "designated by the Congress"), ("PL75", 27241, 27277, "February 13, 2026")),
    "mechanism_4": (("PL37", 114, 127, "continuing appropriations"), ("PL37", 643, 657, "rate for operations")),
    "mechanism_5": (("PL37", 114, 222, "continuing appropriations"), ("PL37", 296, 361, "Payments")),
    "recon_1": (("PL37", 2560, 2667, "Food and Drug Administration"),),
    "recon_2": (("PL74", 2144, 2380, "National Aeronautics and Space Administration"),),
    "recon_3": (("PL37", 2075, 2170, "Rural Water and Waste Disposal"), ("PL37", 3240, 3247, "Rural Utilities Service")),
    "recon_4": (("PL74", 7466, 7758, "State and Tribal Assistance Grants"),),
    "recon_5": (("PL75", 15748, 16078, "Internal Revenue Service"),),
    "summary_1": (("PL37", 2554, 2655, "Food and Drug Administration"),),
    "summary_2": (("PL74", 3474, 5209, "Energy and Water Development"),),
    "summary_3": (("PL37", 2075, 2147, "Rural Water"), ("PL74", 3490, 4201, "civil works"), ("PL74", 7466, 7818, "water infrastructure")),
    "summary_4": (("PL37", 105, 222, "continuing appropriations"), ("PL75", 27246, 27267, "February 13, 2026")),
    "summary_5": (("PL75", 8780, 13656, "TRANSPORTATION, HOUSING AND"),),
}


def _stable_id(prefix: str, kind: str, statement: str) -> str:
    digest = hashlib.sha1(statement.strip().encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{kind}-{digest}"


def _line_excerpt(source_file: str, line_start: int, line_end: int) -> str | None:
    path = Path(__file__).resolve().parents[3] / source_file
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    excerpt = " ".join(lines[line_start - 1 : min(line_end, line_start + 2)])
    return excerpt[:1200] or None


def _normalise_source_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip().lower()


def _source_slice(source_file: str, line_start: int, line_end: int) -> str | None:
    path = Path(__file__).resolve().parents[3] / source_file
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return " ".join(lines[line_start - 1 : line_end])


_DERIVED_EQUATIONS = {
    "Programmatic allocations reconcile to $6,957,972,000": (
        "$1,171,319,000 + $2,496,766,000 + $601,291,000 + $278,185,000 + "
        "$894,063,000 + $71,758,000 + $688,038,000 + $205,180,000 + "
        "$208,018,000 + $343,354,000 = $6,957,972,000"
    ),
    "The nine top-level NASA account amounts arithmetically sum to $24,438,336,000": (
        "$7,250,000,000 + $935,000,000 + $920,500,000 + $7,783,000,000 + "
        "$4,175,000,000 + $143,000,000 + $3,000,000,000 + $185,336,000 + "
        "$46,500,000 = $24,438,336,000"
    ),
    "The three top-level IRS accounts arithmetically sum to $11,195,365,000": (
        "$3,036,606,000 + $4,999,000,000 + $3,159,759,000 = $11,195,365,000"
    ),
}


def _fact_type(statement: str) -> FactType:
    lowered = statement.lower()
    if "no clean" in lowered or "no single clean" in lowered:
        return "inference"
    if "inference" in lowered or "would require" in lowered:
        return "inference"
    if (
        lowered.startswith(("no ", "does not ", "none "))
        or "no separate" in lowered
        or "do not provide a specific" in lowered
        or "not present in the identified" in lowered
        or "does not state a new" in lowered
        or "no dollar amount" in lowered
    ):
        return "absence"
    if any(token in lowered for token in ("sum to", "reconcile", "can be summed", "arithmetically")):
        return "derived"
    if any(token in lowered for token in ("should explain", "answer should", "be concise", "should not provide a derived")):
        return "inference"
    return "statutory"


def _default_evidence(statement: str, divisions: Sequence[str], question_id: str = "") -> tuple[SourceEvidence, ...]:
    if question_id in _QUESTION_SOURCES:
        return tuple(
            SourceEvidence(
                bill=bill,
                division=divisions[0] if divisions else "FY2026 appropriations corpus",
                locator=f"{bill}:{line_start}-{line_end} ({anchor})",
                source_file=_BILL_FILE[bill],
                line_start=line_start,
                line_end=line_end,
                anchor=anchor,
                excerpt=_line_excerpt(_BILL_FILE[bill], line_start, line_end),
                source_hash=_BILL_SHA256[bill],
            )
            for bill, line_start, line_end, anchor in _QUESTION_SOURCES[question_id]
        )
    # Unknown registry keys must provide explicit evidence. Guessing a bill or
    # pointing at line 1 would make a criterion look verified when it is not.
    return ()


def _default_scope(divisions: Sequence[str], statement: str = "") -> CorpusScope:
    selected = tuple(_DIVISION_BILL.get(division, "FY2026 corpus") for division in divisions)
    bills = tuple(dict.fromkeys(bill for value in selected for bill in value.split("/")))
    lowered = statement.lower()
    if "fy2026 laws" in lowered or "complete checked-in fy2026" in lowered:
        bills = ("PL37", "PL74", "PL75")
    return CorpusScope(
        bills=bills or ("PL37", "PL74", "PL75"),
        divisions=tuple(divisions),
        description="Complete checked-in FY2026 bill text for the selected Division(s)",
        source_files=tuple(_BILL_FILE[bill] for bill in (bills or ("PL37", "PL74", "PL75"))),
        complete=True,
        search_query=(f"search complete FY2026 corpus for: {statement}" if statement else "search complete FY2026 corpus"),
    )


@dataclass(frozen=True)
class GoldReference:
    """Typed benchmark criteria with legacy text accessors.

    ``required_facts`` and ``prohibited_errors`` intentionally remain text
    lists so older runner code keeps working.  New judge code should call
    :meth:`to_judge_payload`, which includes stable IDs, weights, types, and
    provenance metadata.
    """

    required_facts: list[str | GoldFact] = field(default_factory=list)
    prohibited_errors: list[str | GoldRule] = field(default_factory=list)
    expected_answer_mode: str = ""
    expected_divisions: list[str] = field(default_factory=list)
    notes: str = ""
    structural_rules: list[AnswerShapeRule | str] = field(default_factory=list)
    allowed_alternatives: list[GoldAlternative] = field(default_factory=list)
    reviewer: str = "2026-07-16 audit"
    verified_on: str = "2026-07-16"

    def _typed_facts(self, question_id: str | None = None) -> tuple[GoldFact, ...]:
        prefix = question_id or self._question_id()
        return tuple(self._fact_from_value(value, index, prefix) for index, value in enumerate(self.required_facts, 1))

    @property
    def facts(self) -> tuple[GoldFact, ...]:
        return self._typed_facts()

    @property
    def errors(self) -> tuple[GoldRule, ...]:
        return tuple(self._rule_from_value(value, index) for index, value in enumerate(self.prohibited_errors, 1))

    def _fact_from_value(self, value: Any, index: int, prefix: str = "gold") -> GoldFact:
        if isinstance(value, GoldFact):
            return value
        if isinstance(value, Mapping):
            return GoldFact(**value)
        statement = str(value)
        fact_id = _stable_id(prefix, "fact", statement)
        fact_type = _fact_type(statement)
        scope = _default_scope(self.expected_divisions, statement) if fact_type == "absence" else None
        return GoldFact(
            id=fact_id,
            statement=statement,
            weight=2 if index == 1 else 1,
            fact_type=fact_type,
            evidence=_default_evidence(statement, self.expected_divisions, prefix),
            corpus_scope=scope,
            equation=(
                next((equation for key, equation in _DERIVED_EQUATIONS.items() if statement.startswith(key)), None)
                if fact_type == "derived"
                else None
            ),
        )

    def _rule_from_value(self, value: Any, index: int, prefix: str | None = None) -> GoldRule:
        if isinstance(value, GoldRule):
            return value
        if isinstance(value, Mapping):
            return GoldRule(**value)
        return GoldRule(
            id=_stable_id(prefix or self._question_id(), "error", str(value)),
            statement=str(value),
            evidence=_default_evidence(str(value), self.expected_divisions, prefix or self._question_id()),
        )

    def _question_id(self) -> str:
        # GoldReference is intentionally usable outside the registry; callers
        # that need stable registry IDs pass question_id to to_judge_payload.
        explicit = getattr(self, "_registry_key", None)
        if explicit:
            return explicit
        registry = globals().get("GOLD_REFERENCES", {})
        for key, value in registry.items():
            if value is self:
                return key
        return "gold"

    def to_judge_payload(self, question_id: str | None = None) -> dict[str, Any]:
        prefix = question_id or self._question_id()
        facts = [asdict(fact) for fact in self._typed_facts(prefix)]
        errors = [asdict(self._rule_from_value(value, index, prefix)) for index, value in enumerate(self.prohibited_errors, 1)]
        structural = [
            asdict(rule) if isinstance(rule, AnswerShapeRule) else {"id": f"{prefix}-shape-{index:02d}", "statement": rule}
            for index, rule in enumerate(self.structural_rules, 1)
        ]
        return {
            "required_facts": facts,
            "prohibited_errors": errors,
            "structural_rules": structural,
            "allowed_alternatives": [asdict(item) for item in self.allowed_alternatives],
            "expected_answer_mode": self.expected_answer_mode,
            "expected_divisions": list(self.expected_divisions),
            "notes": self.notes,
        }

def validate_gold_references(
    references: Mapping[str, GoldReference] | None = None,
    questions: Sequence[Any] | None = None,
) -> None:
    """Fail fast when the benchmark registry is incomplete or untraceable."""
    refs = GOLD_REFERENCES if references is None else references
    if questions is None:
        from tests.evals.questions import EVAL_QUESTIONS

        questions = EVAL_QUESTIONS
    expected = {question.id: question for question in questions}
    missing = sorted(set(expected) - set(refs))
    extra = sorted(set(refs) - set(expected))
    if missing or extra:
        raise ValueError(f"Gold References must exactly cover questions; missing={missing}, extra={extra}")
    seen_ids: set[str] = set()
    repo_root = Path(__file__).resolve().parents[3]
    source_lines: dict[str, list[str]] = {}
    source_hashes: dict[str, str] = {}

    def _lines(source_file: str) -> list[str]:
        if source_file not in source_lines:
            source_lines[source_file] = (repo_root / source_file).read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines()
        return source_lines[source_file]

    def _source_hash(source_file: str) -> str:
        if source_file not in source_hashes:
            source_hashes[source_file] = hashlib.sha256(
                (repo_root / source_file).read_bytes()
            ).hexdigest()
        return source_hashes[source_file]

    for question_id, reference in refs.items():
        question = expected[question_id]
        if not reference.reviewer.strip() or not reference.verified_on.strip():
            raise ValueError(f"{question_id}: reviewer and verification date are required")
        if reference.expected_answer_mode != question.answer_mode:
            raise ValueError(f"{question_id}: expected answer mode does not match question")
        if set(reference.expected_divisions) != set(question.divisions):
            raise ValueError(f"{question_id}: expected Divisions do not match question")
        facts = reference._typed_facts(question_id)
        errors = tuple(reference._rule_from_value(value, index, question_id) for index, value in enumerate(reference.prohibited_errors, 1))
        if not facts:
            raise ValueError(f"{question_id}: at least one required fact is required")
        for criterion in (*facts, *errors):
            if criterion.id in seen_ids:
                raise ValueError(f"duplicate Gold criterion id: {criterion.id}")
            seen_ids.add(criterion.id)
            if not criterion.statement.strip():
                raise ValueError(f"{question_id}: empty Gold criterion statement")
            if criterion.weight < 1:
                raise ValueError(f"{question_id}/{criterion.id}: weight must be positive")
            if criterion.verification_status != "verified":
                raise ValueError(f"{question_id}/{criterion.id}: criterion is not verified")
            if isinstance(criterion, GoldFact):
                if criterion.statement.lower().startswith(("the answer should", "answer should", "should not")):
                    raise ValueError(
                        f"{question_id}/{criterion.id}: answer-shape instructions belong in structural_rules"
                    )
                if criterion.fact_type == "absence":
                    if criterion.corpus_scope is None or not criterion.corpus_scope.bills:
                        raise ValueError(f"{question_id}/{criterion.id}: absence claims require a corpus scope")
                elif not criterion.evidence:
                    raise ValueError(f"{question_id}/{criterion.id}: affirmative facts require source evidence")
                if criterion.fact_type == "derived" and not criterion.equation:
                    raise ValueError(f"{question_id}/{criterion.id}: derived facts require an equation")
            else:
                if "route outside" in criterion.statement.lower():
                    raise ValueError(
                        f"{question_id}/{criterion.id}: routing expectations belong in expected_divisions"
                    )
                if not criterion.evidence:
                    raise ValueError(f"{question_id}/{criterion.id}: prohibited errors require source evidence")
            for evidence in criterion.evidence:
                source_path = repo_root / evidence.source_file
                if not evidence.source_file or not source_path.is_file():
                    raise ValueError(f"{question_id}/{criterion.id}: source file does not exist: {evidence.source_file}")
                if evidence.line_start < 1 or evidence.line_end < evidence.line_start:
                    raise ValueError(f"{question_id}/{criterion.id}: invalid source line range")
                if evidence.line_end > len(_lines(evidence.source_file)):
                    raise ValueError(f"{question_id}/{criterion.id}: source line range exceeds file")
                if not evidence.source_hash or evidence.source_hash != _source_hash(
                    evidence.source_file
                ):
                    raise ValueError(f"{question_id}/{criterion.id}: source file hash has changed")
                expected_excerpt = _line_excerpt(evidence.source_file, evidence.line_start, evidence.line_end)
                if evidence.excerpt != expected_excerpt:
                    raise ValueError(f"{question_id}/{criterion.id}: stored excerpt does not match source range")
                if evidence.anchor:
                    source_slice = _source_slice(evidence.source_file, evidence.line_start, evidence.line_end) or ""
                    if _normalise_source_text(evidence.anchor) not in _normalise_source_text(source_slice):
                        raise ValueError(f"{question_id}/{criterion.id}: source anchor is absent from line range")
            if isinstance(criterion, GoldFact) and criterion.fact_type == "absence" and criterion.corpus_scope:
                if (
                    not criterion.corpus_scope.complete
                    or not criterion.corpus_scope.search_query
                    or not criterion.corpus_scope.source_files
                ):
                    raise ValueError(f"{question_id}/{criterion.id}: absence scope must be complete and searchable")
                for source_file in criterion.corpus_scope.source_files:
                    if not (repo_root / source_file).is_file():
                        raise ValueError(f"{question_id}/{criterion.id}: absence scope file does not exist: {source_file}")
        structural_ids = [
            rule.id if isinstance(rule, AnswerShapeRule) else f"{question_id}-shape-{index:02d}"
            for index, rule in enumerate(reference.structural_rules, 1)
        ]
        if len(structural_ids) != len(set(structural_ids)) or seen_ids.intersection(structural_ids):
            raise ValueError(f"{question_id}: duplicate structural rule id")
        seen_ids.update(structural_ids)

        alternative_ids = {criterion.id for criterion in facts}
        seen_alternative_ids: set[str] = set()
        for alternative in reference.allowed_alternatives:
            if alternative.id in seen_alternative_ids or alternative.id in seen_ids:
                raise ValueError(f"{question_id}: duplicate alternative id: {alternative.id}")
            seen_alternative_ids.add(alternative.id)
            if not alternative.satisfies or not set(alternative.satisfies) <= alternative_ids:
                raise ValueError(f"{question_id}/{alternative.id}: unknown alternative target")


GOLD_REFERENCES: dict[str, GoldReference] = {
    # ------------------------------------------------------------------
    # direct_account_amount
    # ------------------------------------------------------------------

    "direct_1": GoldReference(
        required_facts=[
            "FDA Salaries and Expenses is appropriated $6,957,972,000",
            "Major uses include Human Foods Program, CDER, CBER, CVM, CDRH, NCTR, Center for Tobacco Products, rent/related activities, and other central FDA offices/services",
            "User fees are credited to the account, including prescription drug, medical device, human generic drug, biosimilar, animal drug, generic new animal drug, and tobacco product user fees",
        ],
        prohibited_errors=[
            "Should not add user fees on top of the $6,957,972,000 account amount",
            "Should not include unrelated nearby provisions",
        ],
        structural_rules=[
            AnswerShapeRule(
                id="direct_1-shape-no-internal-language",
                statement="Do not expose internal pipeline terms such as extracted facts, mapped facts, or source chunks.",
            ),
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="Compact account amount/use question. Do not turn this into reconciliation mode.",
    ),

    "direct_2": GoldReference(
        required_facts=[
            "Food Safety and Inspection Service is appropriated $1,215,200,000",
            "The funding carries out services authorized by the Federal Meat Inspection Act, Poultry Products Inspection Act, and Egg Products Inspection Act",
            "$1,000,000 may be credited to the account from laboratory accreditation fees",
            "Major activities include inspection and enforcement for meat, poultry, and egg products",
            "The humane methods of slaughter provision supports inspection/enforcement staffing of no fewer than 148 FTE; it is a staffing proviso, not a separate appropriation",
        ],
        prohibited_errors=[
            "Should not treat the $10,000 representation allowance cap as a separate major appropriation",
            "Should not add the $1,000,000 laboratory accreditation fees as a separate appropriation without saying they may be credited to the account",
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="Amount + activities. The $10,000 is a cap; the $1,000,000 is credited fee authority.",
    ),

    "direct_3": GoldReference(
        required_facts=[
            "NASA Science is appropriated $7,250,000,000",
            "The funding is for necessary expenses in the conduct and support of science research and development activities",
            "The funding remains available until September 30, 2027",
        ],
        prohibited_errors=[
            "Should not include unrelated NASA accounts such as Aeronautics, Exploration, Space Operations, SSMS, Construction, or OIG",
            "Should not compute a NASA-wide total",
            "Should not confuse NASA Science with another NASA account",
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
        ],
        notes="One named NASA account only.",
    ),

    "direct_4": GoldReference(
        required_facts=[
            "EPA Environmental Programs and Management is appropriated $3,114,671,000",
            "The funding remains available until September 30, 2027",
            "The account supports necessary expenses for personnel, travel, passenger motor vehicles, aircraft, reprints, library memberships, and administrative costs",
            "The account supports administrative costs of the brownfields program and implementation of a coal combustion residual permit program",
            "The account includes a $20,000,000 Alaska program and a separate $9,000,000 Toxic Substances Control Act amount",
        ],
        prohibited_errors=[
            "Should not imply the full $3,114,671,000 is brownfields cleanup funding",
            "Should not add set-asides on top of the parent account total",
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
        ],
        notes="Direct account amount with a compact support-purpose summary. Geographic Programs ($690,202,000), Energy Star, grants/training, and National Priorities are supporting examples within the parent account, not mandatory details.",
    ),

    "direct_5": GoldReference(
        required_facts=[
            "The VA Medical Services heading provides $59,858,000,000 plus reimbursements, available October 1, 2026 through September 30, 2027",
            "$75,039,000,000 became available October 1, 2025, and $15,889,000,000 is rescinded from that earlier tranche",
            "Covered services include priority medical treatment and basic medical benefits for veterans in priority groups 1 through 6",
            "The heading covers prescription drugs and prosthetics; the section 251 service list is pooled across Medical Services, Medical Community Care, Medical Support and Compliance, Medical Facilities, and Cost of War Toxic Exposures rather than attributable solely to Medical Services",
            "The pooled service list includes women veterans care, suicide prevention, caregiver support, PTSD services, rural health care, homelessness programs, telehealth, opioid prevention and treatment, and intimate partner violence assistance",
        ],
        prohibited_errors=[
            "Should not present $59,858,000,000 as the only FY2026-relevant tranche without explaining its October 1, 2026 availability and the earlier $75,039,000,000 tranche",
            "Should not attribute the pooled section 251 service list solely to VA Medical Services or merge other VA medical accounts into its heading",
        ],
        structural_rules=[
            AnswerShapeRule(
                id="direct_5-shape-no-internal-language",
                statement="Do not expose internal pipeline terminology in the final answer.",
            ),
        ],
        expected_answer_mode="direct_account_amount",
        expected_divisions=[
            "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES",
        ],
        notes="Gold should allow a careful uncertainty phrase, but not internal pipeline wording.",
    ),

    # ------------------------------------------------------------------
    # broad_topic_total
    # ------------------------------------------------------------------

    "broad_1": GoldReference(
        required_facts=[
            "No single clean FY2026 total is available because the funding mixes appropriated grant/subsidy amounts, loan subsidy cost, direct loan authority, guaranteed loan authority, and authorization changes",
            "USDA Rural Utilities Service Rural Water and Waste Disposal Program Account is a core controlling account",
            "USDA RUS includes $445,864,564 for the cost of direct loans, loan guarantees, and grants",
            "USDA RUS includes $1,015,000,000 in direct loan authority and $50,000,000 in guaranteed loan authority",
            "USDA rural water and waste technical assistance grants include $35,000,000",
            "EPA State and Tribal Assistance Grants include Clean Water SRF capitalization grants of $1,638,861,000",
            "EPA State and Tribal Assistance Grants include Drinking Water SRF capitalization grants of $1,126,101,000",
            "EPA includes $35,000,000 for U.S.-Mexico border water and wastewater facilities",
            "EPA includes $39,000,000 for Alaska rural and Alaska Native Village drinking water and wastewater infrastructure needs",
            "EPA WIFIA includes $64,634,000 for the cost of direct loans and guaranteed loans",
            "EWD includes a Northwestern New Mexico Rural Water Projects Act authorization increase from $870,000,000 to $1,815,000,000, but it is not a clean FY2026 appropriation",
        ],
        prohibited_errors=[
            "Should not present one clean additive total",
            "Should not add USDA loan authority to USDA subsidy/grant budget authority",
            "Should not add STAG total to SRF sub-buckets or project-specific suballocations",
            "Should not treat WIFIA loan subsidy cost and WIFIA principal cap as additive",
            "Should not omit EPA/Interior for rural water or wastewater infrastructure",
            "Should not treat an authorization increase as directly available FY2026 appropriations",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
            "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
        ],
        notes="Key cross-division broad-topic benchmark. Reward grouped funding lanes and financial-type labels.",
    ),

    "broad_2": GoldReference(
        required_facts=[
            "Community Development Fund is $6,995,244,120, including $3,300,000,000 for Community Development Block Grants available to States and units of general local government",
            "HOME Investment Partnerships receives $1,250,000,000",
            "THUD provides separate FY2026 funding streams for rental assistance and homelessness services",
            "Tenant-based rental assistance is appropriated $34,438,557,000",
            "Project-based rental assistance is provided $18,143,000,000",
            "Homeless Assistance Grants receive $4,417,000,000",
            "Homeless Assistance Grants include $290,000,000 for Emergency Solutions Grants",
            "Homeless Assistance Grants include $4,010,000,000 for Continuum of Care and rural housing stability assistance",
            "Homelessness services include $107,000,000 for youth homelessness demonstration projects",
            "Supportive housing for persons with disabilities includes $287,000,000 for Section 811 project rental assistance and associated supportive services",
            "Public Housing Fund at $8,319,393,000 is broader affordable-housing support, not the same as rental assistance or homelessness funding",
        ],
        prohibited_errors=[
            "Should not present a single clean city housing total",
            "Should not add renewal amounts, advance appropriations, and parent amounts without explaining timing and hierarchy",
            "Should not omit homelessness services when the question asks affordable housing, rental assistance, or homelessness services",
            "Should not omit the main Homeless Assistance Grants parent account when answering homelessness services",
            "Should not omit CDBG or HOME when answering a city-facing affordable-housing question",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
        ],
        notes="The answer should be organized by HUD program/funding lane, not as one additive total.",
    ),

    "broad_3": GoldReference(
        required_facts=[
            "Airport infrastructure funding is available through airport grants in THUD",
            "Airport and Airway Trust Fund grants-in-aid for airport planning and development are $4,000,000,000",
            "The $4,000,000,000 supports grants-in-aid for airport planning and development, runway incursion prevention devices and systems, and related airport safety activities",
            "Additional Grants-In-Aid for Airports amount is $577,356,000",
            "$542,356,000 is for Community Project Funding or Congressionally Directed Spending for airport projects",
            "Up to $35,000,000 is for discretionary grants to airports for eligible projects",
            "$542,356,000 and $35,000,000 are suballocations within the $577,356,000 airport-grants heading",
        ],
        prohibited_errors=[
            "Should not add $542,356,000 and $35,000,000 on top of the $577,356,000 parent amount",
            "Should not claim a clean total unless it clearly explains the relationship between the $4,000,000,000 and $577,356,000 buckets",
            "Should not claim an affirmative terminal-upgrade construction amount when the checked-in corpus provides only administrative Airport Terminal Program support and a narrow baggage-reconfiguration reference",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
        ],
        notes="A clean sum of the two top-level airport buckets may be acceptable only if the answer clearly does not double-count suballocations. Do not turn administrative Airport Terminal Program support into terminal construction.",
    ),

    "broad_4": GoldReference(
        required_facts=[
            "Local law enforcement, community violence prevention, and police hiring funding is primarily in OJP and COPS",
            "OJP is $2,400,000,000",
            "OJP includes $964,000,000 for the Edward Byrne Memorial JAG program",
            "OJP includes $84,000,000 for police-community relations, including $50,000,000 for community violence intervention and prevention",
            "COPS programs total $800,000,000",
            "COPS includes $253,093,613 for hiring and rehiring additional career law enforcement officers",
            "COPS includes $18,000,000 for community policing development",
            "COPS includes $15,000,000 for de-escalation training",
            "COPS includes $32,000,000 for Tribal law enforcement hiring and activities",
            "Other targeted grants include $5,000,000 for cybercrimes against individuals and $7,500,000 for the Daniel Anderl Judicial Security and Privacy Act grant program",
        ],
        prohibited_errors=[
            "Should not present one clean additive total of all listed figures",
            "Should not add nested COPS program amounts on top of the $800,000,000 COPS total",
            "Should not add Byrne JAG on top of OJP as if it were separate from OJP",
            "Should not omit either OJP/Byrne JAG or COPS hiring/community violence funding",
            "Should not attribute the OJP $84,000,000 police-community-relations or $50,000,000 community-violence lines to COPS",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
        ],
        notes="Must preserve parent-child relationships for OJP/JAG and COPS subprograms.",
    ),

    "broad_5": GoldReference(
        required_facts=[
            "No clean division-wide total is supported because amounts mix separate accounts, grants, and broader management funding",
            "Hazardous Substance Superfund is $282,749,000 for necessary expenses to carry out CERCLA, including cleanup activities",
            "CERCLA section 104(k) brownfields grants are $98,000,000",
            "CERCLA section 128 grants are $46,250,000",
            "Superfund-related activities under CERCLA sections 311(a) and 126(g) are $77,100,000",
            "Environmental Programs and Management is $3,114,671,000 and includes administrative costs of the brownfields program, but it is broader than cleanup funding",
            "Leaking Underground Storage Tank Trust Fund Program receives $88,903,000, including $64,583,000 for cleanup activities",
            "EPA may collect and obligate brownfields-related fees under CERCLA section 3024, but no dollar amount is provided",
        ],
        prohibited_errors=[
            "Should not present one clean additive brownfields/Superfund/remediation total",
            "Should not imply the full Environmental Programs and Management account is cleanup funding",
            "Should not treat fee authority with no stated dollar amount as a quantified funding line",
            "Should not omit Hazardous Substance Superfund or brownfields grants",
        ],
        expected_answer_mode="broad_topic_total",
        expected_divisions=[
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
        ],
        notes="Good answer separates direct cleanup/remediation accounts from broader EPM support.",
    ),

    # ------------------------------------------------------------------
    # funding_mechanism_no_amount
    # ------------------------------------------------------------------

    "mechanism_1": GoldReference(
        required_facts=[
            "DHS funding is handled through continuing appropriations rather than a full-year DHS appropriation",
            "The continuing resolution uses a rate-for-operations framework tied to prior-year appropriations",
            "The continuing appropriations authority is extended through February 13, 2026",
            "No consolidated full-year DHS dollar amount is provided in the FY2026 laws",
        ],
        prohibited_errors=[
            "Should not hallucinate a full-year DHS amount",
            "Should not add DHS component extensions into a DHS total",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Override current classifier if it says broad_topic_total. This is a no-explicit-amount CR mechanism question.",
    ),

    "mechanism_2": GoldReference(
        required_facts=[
            "The Further Continuing Appropriations Act, 2026 extends continuing appropriations for FY2026",
            "It changes or extends the operative expiration date to February 13, 2026 in the continuing appropriations framework",
            "It is a continuing resolution measure, not a full-year appropriations bill",
            "The core continuing appropriations mechanism is rate for operations under FY2025 appropriations acts and conditions",
            "The identified Act does not state a new consolidated full-year dollar total",
        ],
        prohibited_errors=[
            "Should not invent a total dollar amount for the Further Continuing Appropriations Act",
            "Should not treat the CR as a normal full-year appropriations division",
            "Should not omit rate-for-operations language",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Even though the question is explanatory, the important behavior is mechanism-with-no-new-total.",
    ),

    "mechanism_3": GoldReference(
        required_facts=[
            "No explicit FEMA Disaster Relief Fund dollar total was found in the FY2026 continuing appropriations text",
            "FEMA Disaster Relief Fund is handled through continuing appropriations rather than a new explicit DRF dollar figure",
            "The continuing appropriations period is extended to February 13, 2026",
            "DRF amounts may be apportioned up to the rate for operations necessary for Stafford Act response and recovery activities",
            "The mechanism uses FY2025 appropriations acts as the reference for the rate-for-operations framework",
            "Prior disaster-relief designations are preserved for amounts incorporated by reference",
        ],
        prohibited_errors=[
            "Should not invent a new FY2026 DRF dollar amount",
            "Should not substitute unrelated FEMA amounts from elsewhere",
            "Should not present a FEMA total without a source-backed current-year amount",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Classic mechanism/no-explicit-dollar test.",
    ),

    "mechanism_4": GoldReference(
        required_facts=[
            "The identified FY2026 continuing-appropriations provisions do not provide a specific CISA dollar amount",
            "The generic continuing-appropriations mechanism can be applied to CISA only as an inference; the identified provisions do not name a CISA line item",
            "The continuing resolution date is extended to February 13, 2026",
            "Funding uses FY2025 rate-for-operations language",
            "A CISA dollar total would require a separate line-item appropriation or referenced baseline not present in the identified FY2026 provisions",
        ],
        prohibited_errors=[
            "Should not hallucinate a CISA dollar amount",
            "Should not substitute a broader DHS amount for CISA",
            "Should not treat CR extension language as a dollar amount",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Should answer the either/or directly: only mechanism, no specific CISA amount.",
    ),

    "mechanism_5": GoldReference(
        required_facts=[
            "Agencies or accounts covered by the continuing-resolution provisions without full-year appropriations continue operating under the Act",
            "They continue at the FY2025 rate and under the authority and conditions of applicable FY2025 appropriations Acts",
            "The continuation applies to continuing projects and activities through the date specified in section 106(3)",
            "They may continue only at the most limited funding action permitted",
            "Apportionment limits the continuation to the rate and amounts authorized; the mechanism does not create a new full-year total",
            "The Act allows certain payments and obligations to continue, including personnel pay and benefits, mandatory payments, essential activities to protect life and property, and orderly termination of government functions",
            "Payments and reimbursements are made only to the extent and in the amounts provided in advance in appropriations Acts",
        ],
        prohibited_errors=[
            "Should not provide a new dollar amount",
            "Should not imply agencies receive a full-year appropriation",
            "Should not omit the FY2025 rate/authority/conditions concept",
        ],
        expected_answer_mode="funding_mechanism_no_amount",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="This is explanatory, but for eval purposes it should test CR mechanism behavior.",
    ),

    # ------------------------------------------------------------------
    # reconciliation_breakdown
    # ------------------------------------------------------------------

    "recon_1": GoldReference(
        required_facts=[
            "FDA Salaries and Expenses total appropriation is $6,957,972,000",
            "Programmatic breakdown includes Human Foods Program $1,171,319,000",
            "Programmatic breakdown includes CDER $2,496,766,000",
            "Programmatic breakdown includes CBER $601,291,000",
            "Programmatic breakdown includes CVM $278,185,000",
            "Programmatic breakdown includes CDRH $894,063,000",
            "Programmatic breakdown includes NCTR $71,758,000",
            "Programmatic breakdown includes Center for Tobacco Products $688,038,000",
            "Programmatic breakdown includes Rent and Related $205,180,000",
            "Programmatic breakdown includes GSA rent payments $208,018,000",
            "Programmatic breakdown includes Other activities $343,354,000",
            "Programmatic allocations reconcile to $6,957,972,000",
            "Financing-source breakdown includes prescription drug user fees $1,556,039,000",
            "Financing-source breakdown includes medical device user fees $478,166,000",
            "Financing-source breakdown includes human generic drug user fees $670,900,000",
            "Financing-source breakdown includes biosimilar biological product user fees $55,841,000",
            "Financing-source breakdown includes animal drug user fees $36,152,000",
            "Financing-source breakdown includes generic new animal drug user fees $26,724,000",
            "Financing-source breakdown includes tobacco product user fees $712,000,000",
            "User-fee amounts are credited to the same account and should not be added on top of the account total",
            "$15,000,000 foreign seafood inspections is within Human Foods",
            "$10,000,000 foreign inspection pilots is within CDER",
            "$44,400,000 White Oak Consolidation is within Rent and Related",
            "$25,000 is a ceiling on official reception and representation expenses",
            "$2,000,000 is a transfer cap, not new budget authority",
            "$1,500,000 transfer to HHS OIG is not a separate addition to FDA Salaries and Expenses",
            "FY2027 user fees accepted in FY2026 are excluded from FY2026 amounts under this heading",
        ],
        prohibited_errors=[
            "Should not add user-fee source amounts on top of the $6,957,972,000 account total",
            "Should not classify the $25,000 reception ceiling as a suballocation instead of a cap/limitation",
            "Should not add $44,400,000 White Oak on top of the Rent and Related line",
            "Should not add $15,000,000 or $10,000,000 set-asides on top of their parent lines",
            "Should not surface malformed extraction labels like source cut off or additional user fee source cut off",
            "Should not invent one-to-one mappings between user-fee sources and FDA centers",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="Core reconciliation benchmark. Must separate programmatic allocations from financing-source/user-fee amounts.",
    ),

    "recon_2": GoldReference(
        required_facts=[
            "NASA major accounts include Science $7,250,000,000",
            "NASA major accounts include Aeronautics $935,000,000",
            "NASA major accounts include Space Technology $920,500,000",
            "NASA major accounts include Exploration $7,783,000,000",
            "NASA major accounts include Space Operations $4,175,000,000",
            "NASA major accounts include STEM Engagement $143,000,000",
            "NASA major accounts include Safety, Security and Mission Services $3,000,000,000",
            "NASA major accounts include Construction and Environmental Compliance and Restoration $185,336,000",
            "NASA major accounts include Office of Inspector General $46,500,000",
            "The nine top-level NASA account amounts arithmetically sum to $24,438,336,000",
            "$58,417,135 is Community Project Funding/Congressionally Directed Spending within SSMS, not added separately",
            "$2,500,000 is a set-aside within the $46,500,000 OIG total",
            "$33,000,000 lease-proceeds availability cap is inside CECR and is not standalone budget authority",
            "Up to $38,500,000 may be transferred from SSMS to NASA's Working Capital Fund, but that is transfer authority, not new funding",
            "CECR prior-year project use is limited to not more than 20 percent or $50,000,000, whichever is less",
        ],
        prohibited_errors=[
            "Should not add suballocations such as $58,417,135 or $2,500,000 on top of parent NASA account totals",
            "Should not treat lease proceeds or transfer authority as new appropriations",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
        ],
        notes="NASA reconciliation should identify the arithmetic sum of top-level accounts while keeping suballocations, caps, and transfers non-additive.",
    ),

    "recon_3": GoldReference(
        required_facts=[
            "USDA Rural Water and Waste Disposal Program Account states $1,015,000,000 in direct-loan authority",
            "USDA Rural Water and Waste Disposal Program Account states $50,000,000 in guaranteed-loan authority",
            "USDA Rural Water and Waste Disposal Program Account states $445,864,564 in subsidy/grant budget authority",
            "Direct and guaranteed loan authority total $1,065,000,000",
            "The two explicitly listed TA/circuit-rider lines total $58,900,000: $35,000,000 rural water and waste technical assistance grants plus $23,900,000 circuit rider",
            "$51,476,000 is for direct loans",
            "$3,876,000 is a floor within the $51,476,000 direct-loan set-aside",
            "$1,000,000 is for rural utilities program under section 306(a)(2)(B)",
            "$5,000,000 is for section 306E rural utilities activity",
            "$1,000,000 within section 306E is for subgrants for household decentralized wastewater systems",
            "$7,000,000 is for section 306A(i)(2) grants",
            "$60,000,000 is for loans and grants including water and waste disposal systems grants and Native/tribal/Hawaiian Home Lands purposes",
            "$35,000,000 is for rural water and waste technical assistance grants",
            "$10,000,000 is within the $35,000,000 technical-assistance line",
            "$800,000 is within the $35,000,000 technical-assistance line",
            "$23,900,000 is for the circuit rider program",
            "$4,000,000 is for solid waste management grants",
            "$250,488,564 is a grant line",
            "$110,488,564 is Community Project Funding/Congressionally Directed Spending within the $250,488,564 grant line",
            "$8,000,000 is a transfer to the Rural Utilities Service High Energy Cost Grants Account",
            "0.25 percent management/oversight retention is a cap or limitation",
        ],
        prohibited_errors=[
            "Should not add $1,015,000,000 direct loans, $50,000,000 guaranteed loans, and $445,864,564 subsidy/grant budget authority into one clean pool",
            "Should not add $3,876,000 on top of the $51,476,000 parent line",
            "Should not add $10,000,000 or $800,000 on top of the $35,000,000 technical-assistance parent line",
            "Should not add $110,488,564 on top of the $250,488,564 grant line",
            "Should not treat the $8,000,000 transfer as new funding",
            "Should not treat the 0.25 percent oversight retention as a funding line",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="This is the best test for financial-type labeling: loan authority vs subsidy/grant budget authority vs transfer/cap.",
    ),

    "recon_4": GoldReference(
        required_facts=[
            "EPA State and Tribal Assistance Grants account totals $4,409,609,000",
            "Clean Water SRF capitalization grants are $1,638,861,000",
            "Drinking Water SRF capitalization grants are $1,126,101,000",
            "Safe Drinking Water Act section 1459A(a)-(j) grants are $28,500,000",
            "Safe Drinking Water Act section 1464(d) grants are $28,000,000",
            "STAG includes section 1459B grants of $22,000,000",
            "STAG includes section 1459A(l) grants of $6,500,000",
            "STAG includes FWPCA section 104(b)(8) grants of $25,500,000",
            "STAG includes FWPCA section 221 grants of $41,000,000",
            "STAG includes America's Water Infrastructure Act section 4304(b) grants of $5,400,000",
            "STAG includes Save Our Seas section 302(a) grants of $3,500,000",
            "STAG includes CPF/CDS remediation, construction, and environmental-management projects of $20,364,000; the source does not label this entire lane as water infrastructure",
            "U.S.-Mexico Border high-priority water and wastewater facilities are $35,000,000",
            "Alaska rural and Alaska Native Village drinking water and wastewater infrastructure needs are $39,000,000",
            "SRF and project-specific amounts sit within the broader STAG account structure",
            "The STAG account includes non-water items outside this breakdown",
        ],
        prohibited_errors=[
            "Should not add the $4,409,609,000 STAG total to SRF and project-specific amounts",
            "Should not double-count project-specific amounts that are within the same broader STAG structure",
            "Should not present STAG's full $4,409,609,000 as entirely water infrastructure",
            "Should not assert a derived STAG water subtotal unless the listed components reconcile to it",
            "Should not omit either Clean Water SRF or Drinking Water SRF",
        ],
        structural_rules=[
            AnswerShapeRule(
                id="recon_4-shape-01",
                statement="Do not provide a derived water-infrastructure subtotal unless the answer lists and reconciles every exact source-backed component included.",
            ),
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
        ],
        notes="Do not force a derived water-infrastructure subtotal unless the answer explicitly lists and reconciles the included components.",
    ),

    "recon_5": GoldReference(
        required_facts=[
            "IRS breakdown belongs in Financial Services and General Government",
            "IRS Taxpayer Services receives $3,036,606,000",
            "IRS Enforcement receives $4,999,000,000",
            "IRS Technology and Operations Support receives $3,159,759,000",
            "No separate FY2026 dollar amount for Business Systems Modernization appears in the complete checked-in FY2026 text",
            "No statutory IRS parent total is stated in the complete checked-in FY2026 text",
            "The three top-level IRS accounts arithmetically sum to $11,195,365,000",
            "$7,000,000 is within the Taxpayer Advocate Service amount for identity theft and refund fraud casework",
            "$250,000,000 remains available within Enforcement and is not added on top",
            "$60,257,000 is within Enforcement for the Interagency Crime and Drug Enforcement program",
            "Enforcement includes not more than $35,000,000 for Criminal Investigation investigative technology",
            "$275,000,000 remains available within Technology and Operations Support and is not added on top",
            "$10,000,000 is within Technology and Operations Support for equipment and facilities acquisition",
            "$1,000,000 is within Technology and Operations Support for research",
            "$20,000 is within Technology and Operations Support for official reception and representation expenses",
            "Transfer authority of up to 5 percent of IRS funds is a limitation on use, not a separate FY2026 funding amount",
        ],
        prohibited_errors=[
            "Should not invent a Business Systems Modernization dollar amount if none appears",
            "Should not add within-account set-asides on top of their parent IRS account amounts",
            "Should not treat the 5 percent transfer authority as new funding",
            "Should not classify official reception and representation as a separate funding line",
        ],
        expected_answer_mode="reconciliation_breakdown",
        expected_divisions=[
            "FINANCIAL SERVICES AND GENERAL GOVERNMENT",
        ],
        notes="Use this to catch hallucinated BSM amounts and parent/child double counting in IRS.",
    ),

    # ------------------------------------------------------------------
    # general_summary
    # ------------------------------------------------------------------

    "summary_1": GoldReference(
        required_facts=[
            "The FY2026 Agriculture division funds FDA salaries and expenses",
            "FDA support includes food, drug, biologic, device, veterinary, tobacco, inspection, and regulatory activities",
            "FDA activities are supported by user fees for prescription drugs, medical devices, human generic drugs, biosimilars, animal drugs, generic new animal drugs, and tobacco products",
        ],
        prohibited_errors=[
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
        ],
        notes="Plain-English summary. Numbers are optional unless directly helpful.",
    ),

    "summary_2": GoldReference(
        required_facts=[
            "Energy and Water Development supports Department of Energy programs and water-related programs",
            "DOE coverage spans Office of Science/basic research, energy research and deployment, NNSA nuclear-security and atomic-energy defense work, environmental cleanup, and grid or emergency-response programs",
            "Water and civil-works coverage includes hydroelectric operations, Bureau of Reclamation projects, and Army Corps navigation, flood-risk, or water infrastructure",
            "The division also supports selected cleanup, flood/coastal emergency, administration, and inspector-general activities",
        ],
        prohibited_errors=[
            "Should not focus only on DOE and omit water/civil works",
            "Should not focus only on water and omit DOE energy programs",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
        ],
        notes="General project/activity summary. No need for numeric totals.",
    ),

    "summary_3": GoldReference(
        required_facts=[
            "Water infrastructure appears across USDA, EPA, and Energy-Water",
            "USDA supports rural water and waste disposal through Rural Utilities Service loans, guarantees, grants, and technical assistance",
            "EPA supports water infrastructure through STAG, Clean Water SRF, Drinking Water SRF, targeted border water/wastewater, Alaska rural and Native Village infrastructure, and WIFIA",
            "Energy-Water includes Bureau of Reclamation or water project activity, including rural water authorization/project material",
            "Energy-Water also includes Army Corps of Engineers civil water infrastructure and related project activity",
        ],
        prohibited_errors=[
            "Should not present one clean total across USDA, EPA, and Energy-Water",
            "Should not omit one of USDA, EPA, or Energy-Water",
            "Should not confuse loan authority, grant funding, loan subsidy cost, and authorization changes",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
            "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
        ],
        structural_rules=[
            AnswerShapeRule(
                id="summary_3-shape-01",
                statement="Explain that these are different funding mechanisms and do not collapse them into a single clean total.",
            ),
        ],
        notes="Summary version of broad_1. Explain landscape without full ledger.",
    ),

    "summary_4": GoldReference(
        required_facts=[
            "Regular appropriations provide full-year funding for specified accounts and programs",
            "Continuing appropriations temporarily extend funding for agencies or accounts without full-year appropriations",
            "Continuing appropriations generally operate at a prior-year rate for operations",
            "Continuing appropriations preserve prior-law authority and conditions for continuing projects and activities",
            "A continuing resolution is not the same as a new full-year line-item appropriation",
        ],
        prohibited_errors=[
            "Should not invent a dollar amount for continuing appropriations",
            "Should not imply continuing appropriations are full-year regular appropriations",
            "Should not omit rate-for-operations concept",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
        ],
        notes="Conceptual explanation. It can mention regular divisions generally, but CRX is the controlling source for continuing appropriations mechanics.",
    ),

    "summary_5": GoldReference(
        required_facts=[
            "Transportation-HUD covers transportation and housing/urban development programs relevant to local governments",
            "Transportation-side activities include airport grants, highway/transit or transportation infrastructure, safety, and related transportation programs",
            "HUD-side activities include tenant-based rental assistance, project-based rental assistance, public housing, homelessness services, supportive housing, and community/housing programs",
            "The division contains distinct accounts and programs rather than one single local-government funding pool",
        ],
        prohibited_errors=[
            "Should not compute a THUD-wide total",
            "Should not omit either transportation or housing/HUD coverage",
        ],
        expected_answer_mode="general_summary",
        expected_divisions=[
            "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
        ],
        structural_rules=[
            AnswerShapeRule(
                id="summary_5-shape-01",
                statement="Keep the answer concise and explanatory rather than a detailed funding ledger.",
            ),
        ],
        notes="Plain-English local-government summary of THUD scope.",
    ),
}
