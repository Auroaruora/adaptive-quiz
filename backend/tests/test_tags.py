"""Tests for tag-based similarity.

The property that matters is not that similar questions score highly —
it is that a question sharing only a common tag does not. Every
derivatives question involves polynomials; sharing that says nothing.
"""

import pytest

from app import tags

# Eighteen questions, so a tag on two of them is rare and one on all
# eighteen is worthless.
USAGE = {
    "polynomial": 9,
    "power-rule": 8,
    "chain-rule": 4,
    "product-rule": 2,
    "quotient-rule": 2,
}
WEIGHTS = tags.tag_weights(USAGE, 18)


class TestTagWeights:
    """Rarer tags have to count for more."""

    def test_a_rare_tag_outweighs_a_common_one(self):
        assert WEIGHTS["product-rule"] > WEIGHTS["polynomial"]

    def test_weights_fall_as_a_tag_becomes_more_common(self):
        ordered = [
            WEIGHTS[t]
            for t in ("product-rule", "chain-rule", "power-rule", "polynomial")
        ]
        assert ordered == sorted(ordered, reverse=True)

    def test_a_tag_on_everything_is_worth_nothing(self):
        weights = tags.tag_weights({"everywhere": 18}, 18)
        assert weights["everywhere"] == pytest.approx(0.0)

    def test_an_unused_tag_is_dropped_rather_than_dividing_by_zero(self):
        assert "never" not in tags.tag_weights({"never": 0}, 18)


class TestSimilarity:
    """How alike two tag sets are."""

    def test_identical_tags_are_maximally_similar(self):
        a = frozenset({"product-rule", "polynomial"})
        assert tags.similarity(a, a, WEIGHTS) == pytest.approx(1.0)

    def test_nothing_shared_means_no_similarity(self):
        assert (
            tags.similarity(
                frozenset({"product-rule"}),
                frozenset({"chain-rule"}),
                WEIGHTS,
            )
            == 0.0
        )

    def test_sharing_a_rare_tag_beats_sharing_a_common_one(self):
        """The whole reason for weighting."""
        rare = tags.similarity(
            frozenset({"product-rule", "polynomial"}),
            frozenset({"product-rule", "chain-rule"}),
            WEIGHTS,
        )
        common = tags.similarity(
            frozenset({"polynomial", "product-rule"}),
            frozenset({"polynomial", "chain-rule"}),
            WEIGHTS,
        )
        assert rare > common

    def test_is_symmetric(self):
        a = frozenset({"power-rule", "polynomial"})
        b = frozenset({"power-rule", "chain-rule"})
        assert tags.similarity(a, b, WEIGHTS) == pytest.approx(
            tags.similarity(b, a, WEIGHTS)
        )

    def test_extra_unshared_tags_dilute_the_score(self):
        """Dividing by the union, not just counting shared tags.

        Otherwise a broadly tagged question looks similar to everything.
        """
        focused = tags.similarity(
            frozenset({"product-rule"}),
            frozenset({"product-rule"}),
            WEIGHTS,
        )
        padded = tags.similarity(
            frozenset({"product-rule"}),
            frozenset({"product-rule", "chain-rule", "polynomial"}),
            WEIGHTS,
        )
        assert padded < focused

    def test_two_questions_sharing_only_a_worthless_tag_score_zero(self):
        weights = tags.tag_weights({"everywhere": 18, "rare": 2}, 18)
        assert tags.similarity(
            frozenset({"everywhere"}), frozenset({"everywhere"}), weights
        ) == pytest.approx(0.0)


class TestWeakness:
    """Turning mistakes into a picture of what is weak."""

    def test_no_mistakes_gives_an_empty_profile(self):
        assert tags.weakness([]) == {}

    def test_a_tag_across_two_mistakes_outweighs_one_seen_once(self):
        profile = tags.weakness(
            [
                (frozenset({"product-rule", "trig"}), 1.0),
                (frozenset({"product-rule", "polynomial"}), 1.0),
            ]
        )
        assert profile["product-rule"] > profile["trig"]

    def test_urgency_carries_through(self):
        fresh = tags.weakness([(frozenset({"chain-rule"}), 1.0)])
        faded = tags.weakness([(frozenset({"chain-rule"}), 0.05)])
        assert fresh["chain-rule"] > faded["chain-rule"]


class TestAffinity:
    """Scoring a candidate against a student's weaknesses."""

    def test_a_student_with_no_mistakes_scores_everything_zero(self):
        """Which is what makes the first question need no special case."""
        assert tags.affinity(frozenset({"product-rule"}), {}, WEIGHTS) == 0.0

    def test_a_question_matching_the_weak_tag_scores_highest(self):
        profile = tags.weakness([(frozenset({"product-rule"}), 1.0)])
        matching = tags.affinity(
            frozenset({"product-rule", "polynomial"}), profile, WEIGHTS
        )
        unrelated = tags.affinity(
            frozenset({"chain-rule", "polynomial"}), profile, WEIGHTS
        )
        assert matching > unrelated

    def test_sharing_nothing_with_the_profile_scores_zero(self):
        profile = tags.weakness([(frozenset({"product-rule"}), 1.0)])
        assert tags.affinity(frozenset({"chain-rule"}), profile, WEIGHTS) == 0.0
