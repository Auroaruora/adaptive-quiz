"""How alike two questions are, and what a student keeps getting wrong.

Pure functions — no database. Similarity is tag-set overlap, weighted so
that sharing a rare tag counts for more than sharing a common one: every
derivatives question is about polynomials, but only two are about the
quotient rule, so the second tells you far more.

A question with one unshared tag is as isolated as it would be under a
single-skill scheme. The authoring rule that prevents it is in
`docs/data-model.md`: at least two tags, at least one of them broad.
"""

import math
from collections.abc import Iterable, Mapping
from collections.abc import Set as AbstractSet


def tag_weights(
    usage: Mapping[str, int], total_questions: int
) -> dict[str, float]:
    """Scores each tag by how much sharing it says.

    A tag on every question distinguishes nothing and scores near zero; a
    tag on two questions out of eighteen scores highly. This is inverse
    document frequency, borrowed from text search for the same reason.

    Args:
        usage: How many questions carry each tag.
        total_questions: Questions the usage counts were taken over.

    Returns:
        A weight per tag, higher for rarer tags.
    """
    return {
        tag: math.log(total_questions / count)
        for tag, count in usage.items()
        if count > 0
    }


def similarity(
    left: AbstractSet[str],
    right: AbstractSet[str],
    weights: Mapping[str, float],
) -> float:
    """How alike two questions are, from their tags.

    A weighted Jaccard: shared weight over total weight. Dividing by the
    union rather than counting raw overlap stops a heavily tagged
    question from looking similar to everything.

    Args:
        left: One question's tags.
        right: The other's.
        weights: Per-tag weights from `tag_weights`.

    Returns:
        0.0 when nothing is shared, 1.0 for identical tag sets.
    """
    shared = left & right
    if not shared:
        return 0.0
    union = sum(weights.get(tag, 0.0) for tag in left | right)
    if union == 0.0:
        return 0.0
    return sum(weights.get(tag, 0.0) for tag in shared) / union


def weakness(
    mistakes: Iterable[tuple[AbstractSet[str], float]],
) -> dict[str, float]:
    """Builds a picture of what a student keeps getting wrong, by tag.

    Each mistake contributes its urgency to every tag the missed question
    carried. A tag that shows up across several recent mistakes ends up
    heaviest, which is what "getting this wrong more often" means once
    it is spread across questions rather than tied to one.

    Args:
        mistakes: Pairs of (tags of the missed question, its urgency).

    Returns:
        A weight per tag. Empty when there are no mistakes.
    """
    profile: dict[str, float] = {}
    for question_tags, urgency in mistakes:
        for tag in question_tags:
            profile[tag] = profile.get(tag, 0.0) + urgency
    return profile


def affinity(
    question_tags: AbstractSet[str],
    profile: Mapping[str, float],
    weights: Mapping[str, float],
) -> float:
    """How well a question answers what a student is getting wrong.

    Args:
        question_tags: Tags of the question being considered.
        profile: Weakness profile from `weakness`.
        weights: Per-tag weights from `tag_weights`.

    Returns:
        Zero when the question shares nothing with the student's
        mistakes, which is also what a student with no mistakes sees for
        every question — so selection falls back to difficulty on its
        own, with no special case.
    """
    return sum(
        profile.get(tag, 0.0) * weights.get(tag, 0.0) for tag in question_tags
    )
