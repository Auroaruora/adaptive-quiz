"""Rasch (one-parameter logistic) model driving ability and difficulty.

Pure functions only — nothing here touches the database, the API, or the
clock, so every update can be unit-tested and replayed in isolation.

Ability (theta) and item difficulty (b) share one logit scale, and only
their difference matters: a student meets a question they have an even
chance of answering when theta equals b.
"""

import bisect
import dataclasses
import enum
import math

#: Step size for ability. Held constant rather than decayed, because a
#: decaying rate assumes the quantity being estimated stays put. A student
#: who is learning is precisely the case where it does not, so theta has to
#: keep tracking rather than freeze once it looks settled.
ABILITY_LEARNING_RATE = 0.3

#: Step size for a question that has never been answered.
ITEM_BASE_LEARNING_RATE = 0.3

#: Answers after which the item step size has halved. Item difficulty is
#: stationary — a question does not get harder — so its rate decays on a
#: 1/n schedule, which satisfies the Robbins-Monro conditions and lets b
#: converge instead of drifting forever.
ITEM_RATE_HALF_LIFE = 10.0

#: Both parameters are held inside this range. At a gap of 4 logits the
#: model already predicts ~98%, so wider values say nothing new and only
#: invite runaway drift on thin data.
PARAMETER_MIN = -4.0
PARAMETER_MAX = 4.0


class AbilityLevel(enum.StrEnum):
    """A readable band for an ability estimate.

    A raw logit means nothing to a student, so theta is also reported as
    one of these. The bands are presentation, not model: nothing in the
    update rule reads them.
    """

    DEVELOPING = "developing"
    PROGRESSING = "progressing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"


#: Upper bounds separating the ability bands, in logits.
_LEVEL_THRESHOLDS = (-0.5, 0.5, 1.5)
_LEVELS = (
    AbilityLevel.DEVELOPING,
    AbilityLevel.PROGRESSING,
    AbilityLevel.PROFICIENT,
    AbilityLevel.ADVANCED,
)


def ability_level(theta: float) -> AbilityLevel:
    """Maps an ability estimate onto a readable band.

    Args:
        theta: Student ability, in logits.

    Returns:
        The band containing that ability.
    """
    return _LEVELS[bisect.bisect_right(_LEVEL_THRESHOLDS, theta)]


@dataclasses.dataclass(frozen=True)
class Update:
    """One answer's effect on both parameters.

    The fields mirror the columns of the `attempts` table, so a caller can
    store the result without rearranging it. `p_correct` is the exception:
    it is returned for feedback and debugging but deliberately not stored,
    since it is recomputable from `theta_before` and `b_before`.
    """

    theta_before: float
    theta_after: float
    b_before: float
    b_after: float
    k_theta: float
    k_b: float
    p_correct: float


def probability_correct(theta: float, difficulty: float) -> float:
    """Probability that a student of this ability answers correctly.

    Args:
        theta: Student ability, in logits.
        difficulty: Question difficulty b, in logits.

    Returns:
        A probability in (0, 1). Exactly 0.5 when theta equals difficulty.
    """
    return 1.0 / (1.0 + math.exp(-(theta - difficulty)))


def item_learning_rate(times_answered: int) -> float:
    """Step size for a question's difficulty, given its answer count.

    Args:
        times_answered: Answers this question has already received.

    Returns:
        The step size, falling from ITEM_BASE_LEARNING_RATE toward zero.
    """
    return ITEM_BASE_LEARNING_RATE / (
        1.0 + times_answered / ITEM_RATE_HALF_LIFE
    )


def clamp(value: float) -> float:
    """Holds a parameter inside the representable logit range.

    Args:
        value: An ability or difficulty estimate.

    Returns:
        The value, bounded to [PARAMETER_MIN, PARAMETER_MAX].
    """
    return max(PARAMETER_MIN, min(PARAMETER_MAX, value))


def apply_answer(
    *,
    theta: float,
    difficulty: float,
    times_answered: int,
    is_correct: bool,
) -> Update:
    """Updates both parameters from a single answer.

    Both moves are driven by the same error term, the gap between what
    happened and what the model predicted. A surprising outcome moves the
    estimates a long way; an expected one barely moves them at all. The
    signs are opposite: answering correctly argues the student is stronger
    than thought and the question easier.

    Args:
        theta: Student's current ability in this topic.
        difficulty: Question's current difficulty b.
        times_answered: Answers this question has already received, which
            sets how far its difficulty is still allowed to move.
        is_correct: Whether the student answered correctly.

    Returns:
        An Update holding both parameters either side of the change, the
        step sizes used, and the probability the model predicted.
    """
    p_correct = probability_correct(theta, difficulty)
    k_theta = ABILITY_LEARNING_RATE
    k_b = item_learning_rate(times_answered)
    error = (1.0 if is_correct else 0.0) - p_correct

    return Update(
        theta_before=theta,
        theta_after=clamp(theta + k_theta * error),
        b_before=difficulty,
        b_after=clamp(difficulty - k_b * error),
        k_theta=k_theta,
        k_b=k_b,
        p_correct=p_correct,
    )
