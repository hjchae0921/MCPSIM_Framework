"""Strict records and physical value/region types shared by authoring agents."""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, create_model
from enum import Enum

Text = Annotated[str, Field(min_length=1)]
Dimension = Annotated[int, Field(gt=0)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


Number = Annotated[float, Field(allow_inf_nan=False)]
Vector = Annotated[list[Number], Field(min_length=1)]
Matrix = Annotated[list[Vector], Field(min_length=1)]


class Region(Record):
    name: Text
    dim: Annotated[int, Field(gt=0)]
    tags: Annotated[list[Annotated[int, Field(gt=0)]], Field(min_length=1)]


Value = Number | Vector | Matrix


def region_key(region):
    return region["name"], region["dim"], tuple(sorted(region["tags"]))


COUPLING = ("single_physics", "multi_physics_one_way", "multi_physics_fully_coupled")
CouplingType = Literal["single_physics", "multi_physics_one_way", "multi_physics_fully_coupled"]
ALIASES = {
    "multi_physics_\ub2e8\ubc29\ud5a5": COUPLING[1],
    "multi_physics_\uc591\ubc29\ud5a5": COUPLING[2],
    "multiphysics_one_way": COUPLING[1],
    "multiphysics_fully_coupled": COUPLING[2],
}


def normalized_coupling(value):
    """Translate legacy spellings; leave invalid values for schema validation."""
    return ALIASES.get(value, value) if isinstance(value, str) else value


def generation_schema(value):
    """Keep structural constraints portable; validate array lengths in Python.

    Repeated, bounded arrays can exceed provider grammar limits. This projection
    preserves closed properties, required fields, item types, and allowed values.
    It never changes the Pydantic model used to accept the response.
    """
    if isinstance(value, dict):
        return {
            key: generation_schema(child)
            for key, child in value.items()
            if not (value.get("type") == "array" and key in ("minItems", "maxItems"))
        }
    if isinstance(value, list):
        return [generation_schema(child) for child in value]
    return value


def named_record(label, fields, description=None):
    """Use aliases so physical identifiers and dotted targets stay exact JSON keys."""
    fields = list(fields)
    names = [name for name, _ in fields]
    if len(names) != len(set(names)):
        raise ValueError("Contract field names must be unique.")
    result = create_model(
        label,
        __base__=Record,
        __doc__=description,
        **{
            f"item_{i}": (annotation, Field(alias=name))
            for i, (name, annotation) in enumerate(fields)
        },
    )
    if not fields:
        result.model_config["json_schema_extra"] = {"required": []}
    return result


class Option(Record):
    label: Text
    description: Text


class InputQuestion(Record):
    question_type: Literal["input"]
    question: Text = Field(description="Ask for information needed to resolve the target fields.")
    options: Annotated[
        list[Option], Field(max_length=0, description="Direct input has no alternatives.")
    ]


class ChoiceQuestion(Record):
    question_type: Literal["choice"]
    question: Text = Field(description="Ask the user to choose an alternative for one decision.")
    options: Annotated[
        list[Option],
        Field(
            min_length=1,
            description=(
                "Substantive alternatives, rather than input instructions or settled facts. Use"
                " recommendations for numerical candidates."
            ),
        ),
    ]


class SuggestedValue(Record):
    name: Text
    value: Number | Vector | Matrix
    unit: str


class ValueRecommendation(Option):
    description: Text = Field(
        description=(
            "Explain this numerical proposal and its assumptions, separately from approved facts."
        )
    )
    values: Annotated[
        list[SuggestedValue],
        Field(min_length=1, description="Numerical values and units forming a coherent candidate."),
    ]


class RecommendationQuestion(Record):
    question_type: Literal["recommendation"]
    question: Text = Field(
        description=(
            "Present proposed values and assumptions for review; the user may supply different"
            " values."
        )
    )
    options: Annotated[
        list[ValueRecommendation],
        Field(
            min_length=1,
            max_length=2,
            description=(
                "Distinct numerical candidates; manual entry remains available in the dialogue."
            ),
        ),
    ]


Question = InputQuestion | ChoiceQuestion | RecommendationQuestion


def scoped_questions(label, targets, recommendation_names=(), kind=None):
    """Constrain question targets and numerical suggestions to the active card."""
    if not targets:
        raise ValueError("No fields in the current stage can be questioned.")
    Target = Enum(
        label + "QuestionTarget", {f"field_{i}": p for i, p in enumerate(targets)}, type=str
    )
    fields = {
        "targets": (
            Annotated[
                list[Target],
                Field(min_length=1, description="Unresolved fields in the active card."),
            ],
            ...,
        )
    }
    if kind is not None:
        fields["kind"] = (Literal[kind], ...)
    Input = create_model(
        label + "InputQuestion",
        __base__=InputQuestion,
        question=(
            Text,
            Field(description="Ask for information needed to resolve the target fields."),
        ),
        **fields,
    )
    Choice = create_model(
        label + "ChoiceQuestion",
        __base__=ChoiceQuestion,
        question=(
            Text,
            Field(description="Ask the user to choose an alternative for the target fields."),
        ),
        options=(
            Annotated[
                list[Option],
                Field(
                    min_length=1,
                    description=(
                        "Substantive alternatives for one decision, rather than input instructions"
                        " or settled facts."
                    ),
                ),
            ],
            ...,
        ),
        **fields,
    )
    if not recommendation_names:
        return Input | Choice
    Name = Enum(
        label + "RecommendedName",
        {f"item_{i}": p for i, p in enumerate(recommendation_names)},
        type=str,
    )
    Value = create_model(label + "SuggestedValue", __base__=SuggestedValue, name=(Name, ...))
    OptionModel = create_model(
        label + "ValueOption",
        __base__=ValueRecommendation,
        values=(Annotated[list[Value], Field(min_length=1)], ...),
    )
    Recommendation = create_model(
        label + "RecommendationQuestion",
        __base__=RecommendationQuestion,
        options=(Annotated[list[OptionModel], Field(min_length=1, max_length=2)], ...),
        **fields,
    )
    return Input | Choice | Recommendation
