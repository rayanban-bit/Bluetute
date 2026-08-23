"""
Bluetute — Structured Output Schemas

Pydantic models for every node's output. These are passed to the LLM API
as JSON-schema-constrained output (e.g. Gemini's `response_schema`,
OpenAI/Claude "tool use" / structured output, or Featherless JSON mode)
so every node returns machine-parseable, typed data instead of free text.
This is what makes the workflow reproducible and scoreable against the
benchmark — we diff structured fields, not prose.

Import path used throughout prompts/*.py:
    from schemas.models import ReasoningAnalysis, MisconceptionClassification, ...
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Node 1 — Input Parser
# --------------------------------------------------------------------------- #
class ParsedInput(BaseModel):
    """Normalized student attempt, ready for downstream nodes."""

    problem_statement: str = Field(..., description="The math problem, normalized/cleaned.")
    domain: Literal["Algebra", "Functions", "Geometry", "Probability", "Mixed", "Other"]
    student_final_answer: str
    student_reasoning_steps: list[str] = Field(
        default_factory=list,
        description="Student's shown work, split into discrete steps. Empty list if no work shown.",
    )
    correct_final_answer: Optional[str] = Field(
        None, description="Known correct answer if available (benchmark cases supply this)."
    )
    previous_attempts: list[str] = Field(
        default_factory=list, description="Prior wrong answers/attempts on this problem, if any."
    )
    parse_notes: str = Field(
        "", description="Any ambiguity or cleanup the parser had to resolve."
    )


# --------------------------------------------------------------------------- #
# Node 2 — Reasoning Analyzer
# --------------------------------------------------------------------------- #
class ErrorType(str, Enum):
    CONCEPTUAL = "conceptual"
    EXECUTION = "execution"          # arithmetic/computational slip, method was sound
    INCOMPLETE = "incomplete"        # student stopped before reaching an answer method
    UNKNOWN = "unknown"


class ReasoningStepJudgment(BaseModel):
    step_index: int
    step_text: str
    is_valid: bool
    note: str = Field("", description="Why this step is/isn't valid, if not obvious.")


class ReasoningAnalysis(BaseModel):
    """Output of Node 2. Central job: decide whether the wrong answer stems
    from a conceptual misconception or a mere execution slip BEFORE any
    misconception label is chosen (see taxonomy escape hatches)."""

    step_judgments: list[ReasoningStepJudgment]
    first_invalid_step_index: Optional[int] = Field(
        None, description="Index into step_judgments where reasoning first breaks. Null if no work shown."
    )
    error_type: ErrorType
    evidence: str = Field(
        ..., description="Concise quote/paraphrase of the reasoning that supports error_type."
    )
    confidence: float = Field(..., ge=0.0, le=1.0)


# --------------------------------------------------------------------------- #
# Node 3 — Misconception Classifier
# --------------------------------------------------------------------------- #
class MisconceptionClassification(BaseModel):
    """Output of Node 3. `misconception_id` MUST be one of the ids in
    taxonomy.misconception_taxonomy.TAXONOMY_BY_ID — validate on receipt
    and reject/retry if the model invents a label."""

    misconception_id: str = Field(..., description="Must match an id in the taxonomy.")
    label: str
    domain: str
    evidence: str = Field(..., description="Specific reasoning text that supports this classification.")
    confidence: float = Field(..., ge=0.0, le=1.0)
    alternative_candidate_ids: list[str] = Field(
        default_factory=list,
        description="Other taxonomy ids that were considered plausible, for the Critic to interrogate.",
    )


# --------------------------------------------------------------------------- #
# Node 5 — Adversarial Critic
# --------------------------------------------------------------------------- #
class AlternativeHypothesis(BaseModel):
    misconception_id: str
    supporting_evidence: str
    contradicting_evidence: str
    plausibility: float = Field(..., ge=0.0, le=1.0)


class CriticReview(BaseModel):
    """Output of Node 5. The critic's job is to try to break the initial
    diagnosis, not confirm it. `diagnosis_survives=False` should be common
    enough to be meaningful — if the critic always agrees, it isn't doing
    adversarial work and the eval framework should flag that (see
    docs/evaluation notes on critic-agreement-rate as a sanity metric)."""

    attempted_rebuttal: str = Field(..., description="The critic's strongest case against the initial diagnosis.")
    alternative_hypotheses: list[AlternativeHypothesis] = Field(default_factory=list)
    diagnosis_survives: bool
    survival_rationale: str = Field(..., description="Why the diagnosis does/doesn't survive scrutiny.")
    confidence_adjustment: float = Field(
        ..., description="Delta to apply to original confidence, range -1.0..+1.0 (usually <= 0)."
    )


# --------------------------------------------------------------------------- #
# Node 6 — Diagnosis Selector
# --------------------------------------------------------------------------- #
class FinalDiagnosis(BaseModel):
    """Output of Node 6. No hidden chain-of-thought — evidence field is the
    only justification surfaced, kept short and checkable."""

    misconception_id: str
    error_type: ErrorType
    final_confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_summary: str = Field(..., max_length=500)
    intervention_appropriate: bool = Field(
        ..., description="False if confidence too low / evidence too weak to act on (escalate to unknown)."
    )


# --------------------------------------------------------------------------- #
# Node 7 — Intervention Planner
# --------------------------------------------------------------------------- #
class InterventionStrategy(str, Enum):
    SOCRATIC_QUESTION = "socratic_question"
    HINT = "hint"
    COUNTEREXAMPLE = "counterexample"
    SIMPLER_EXAMPLE = "simpler_example"
    VISUAL_EXPLANATION = "visual_explanation"
    RETEACHING = "reteaching"
    TARGETED_PRACTICE = "targeted_practice"


class InterventionPlan(BaseModel):
    strategy: InterventionStrategy
    rationale: str = Field(..., description="Why this strategy fits the diagnosis + student level.")
    target_misconception_id: str
    difficulty_adjustment: Literal["easier", "same", "harder"] = "same"


# --------------------------------------------------------------------------- #
# Node 8 — Socratic Tutor
# --------------------------------------------------------------------------- #
class TutorMessage(BaseModel):
    message_to_student: str = Field(
        ..., description="Student-facing text. Must not reveal the final answer directly."
    )
    strategy_used: InterventionStrategy
    reveals_answer: bool = Field(
        ..., description="Self-check flag the generator sets; should be False except for 'reteaching' after repeated failure."
    )


# --------------------------------------------------------------------------- #
# Node 9 — Response Evaluator
# --------------------------------------------------------------------------- #
class ResolutionStatus(str, Enum):
    RESOLVED = "MISCONCEPTION_RESOLVED"
    PERSISTS = "MISCONCEPTION_PERSISTS"
    PARTIAL = "PARTIAL_PROGRESS"


class ResponseEvaluation(BaseModel):
    status: ResolutionStatus
    evidence: str
    confidence: float = Field(..., ge=0.0, le=1.0)


# --------------------------------------------------------------------------- #
# Node 11 — Student Model
# --------------------------------------------------------------------------- #
class SkillLevel(str, Enum):
    STRONG = "strong"
    DEVELOPING = "developing"
    WEAK = "weak"
    PERSISTENT_MISCONCEPTION = "persistent_misconception"


class StudentModelEntry(BaseModel):
    topic: str
    domain: str
    level: SkillLevel
    last_misconception_id: Optional[str] = None
    attempts_seen: int = 0
    last_updated: str = Field(..., description="ISO-8601 timestamp")


class StudentModel(BaseModel):
    student_id: str
    entries: list[StudentModelEntry] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Baseline (single-prompt) output — kept structurally comparable for eval
# --------------------------------------------------------------------------- #
class BaselineResponse(BaseModel):
    tutoring_response: str
    claimed_misconception_id: Optional[str] = Field(
        None, description="If the single prompt is asked to also name a misconception id, for apples-to-apples scoring."
    )
