"""Request and response shapes for the API.

Field names are camelCase on the wire and snake_case in Python, so the
TypeScript frontend and the Python backend each read naturally.

Nothing here carries answer-revealing data on a question being asked:
`is_correct`, `misconception`, the worked solution and `difficulty_b`
appear only in the feedback returned after an answer is submitted.
"""

import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.irt import AbilityLevel


class _Wire(BaseModel):
    """Base for everything crossing the wire."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class UserCreate(_Wire):
    """Body of POST /users."""

    display_name: str = Field(min_length=1, max_length=50)


class UserOut(_Wire):
    """A created student. There is no authentication in this project."""

    id: int
    display_name: str
    created_at: datetime.datetime


class TopicOut(_Wire):
    """A topic a student can be quizzed on."""

    id: int
    slug: str
    name: str
    description: str | None
    question_count: int


class TagOut(_Wire):
    """A concept a question exercises."""

    slug: str
    name: str


class OptionOut(_Wire):
    """One answer choice, as shown before answering."""

    id: int
    text: str
    position: int


class QuestionOut(_Wire):
    """A question being asked.

    Deliberately omits which option is correct, every misconception, the
    worked solution, and difficulty_b.

    `tags` are ordered rarest first, so a client showing only one shows
    the most specific: "quotient rule" tells a student more than
    "polynomial", which is true of nearly every question in the topic.
    """

    id: int
    topic_slug: str
    stem: str
    tags: list[TagOut]
    options: list[OptionOut]


class AbilityOut(_Wire):
    """A student's ability in one topic, as a number and a band."""

    theta: float
    level: AbilityLevel


class NextQuestionOut(_Wire):
    """The next question, or a signal that the pool is finished.

    `question` is null exactly when `complete` is true, which means nothing
    is left after the request's narrowing: the topic, the concepts asked
    for, or a session's pool once its exclusions are applied.

    `remaining` counts what that pool could still serve, including the
    question returned, so a session can size its run before it starts.
    """

    question: QuestionOut | None
    ability: AbilityOut
    complete: bool
    remaining: int


class AnswerCreate(_Wire):
    """Body of POST /submit-answer."""

    user_id: int = Field(gt=0)
    question_id: int = Field(gt=0)
    selected_option_id: int = Field(gt=0)


class FeedbackOut(_Wire):
    """What the student is told after answering.

    `misconception` is populated only for a wrong answer, and names the
    specific error that choice encodes.
    """

    is_correct: bool
    correct_option_id: int
    misconception: str | None
    solution: list[str]
    theta_before: float
    theta_after: float


class SubmitAnswerOut(_Wire):
    """Feedback on the answer just given, plus whatever comes next."""

    feedback: FeedbackOut
    next: NextQuestionOut


class WeakSpot(_Wire):
    """A concept the student is currently getting wrong.

    `missed` is the plain count, because "missed 3 times" is readable.
    The ordering carries the decay, so the list is worst-first without
    exposing a weight nobody can interpret.
    """

    slug: str
    name: str
    missed: int


class TopicSummary(_Wire):
    """Headline numbers for one topic.

    `mastered` counts questions whose most recent answer was correct,
    which is the same rule that decides when a topic is complete.
    """

    theta: float
    level: AbilityLevel
    answered: int
    correct: int
    mastered: int
    total: int


class SeriesPoint(_Wire):
    """One answer, for plotting ability over time."""

    at: datetime.datetime
    theta: float
    is_correct: bool


class TopicProgress(_Wire):
    """Everything the dashboard needs for one topic."""

    slug: str
    name: str
    summary: TopicSummary
    weak_spots: list[WeakSpot]
    series: list[SeriesPoint]


class ProgressOut(_Wire):
    """Body of GET /progress/{user_id}."""

    user_id: int
    topics: list[TopicProgress]
