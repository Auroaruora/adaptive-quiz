"""Tests for the Rasch update rule.

These assert behaviour rather than restating the formula: direction,
relative magnitude, convergence, and the boundary where clamping breaks
the arithmetic identity a replay would otherwise rely on.
"""

import math
import random

import pytest

from app import irt


class TestProbabilityCorrect:
    """The logistic response function."""

    def test_even_chance_when_ability_matches_difficulty(self):
        assert irt.probability_correct(0.0, 0.0) == pytest.approx(0.5)
        assert irt.probability_correct(2.5, 2.5) == pytest.approx(0.5)

    def test_only_the_gap_matters_not_the_absolute_values(self):
        assert irt.probability_correct(1.0, 0.0) == pytest.approx(
            irt.probability_correct(3.0, 2.0)
        )

    @pytest.mark.parametrize(
        "gap, expected",
        [(1.0, 0.7311), (2.0, 0.8808), (-1.0, 0.2689), (-2.0, 0.1192)],
    )
    def test_matches_the_published_gap_table(self, gap, expected):
        """Guards the table in docs/data-model.md against drift."""
        assert irt.probability_correct(gap, 0.0) == pytest.approx(
            expected, abs=1e-4
        )

    def test_is_symmetric_about_an_even_chance(self):
        assert irt.probability_correct(1.3, 0.0) + irt.probability_correct(
            -1.3, 0.0
        ) == pytest.approx(1.0)

    def test_rises_with_ability(self):
        values = [irt.probability_correct(t, 0.0) for t in (-2, -1, 0, 1, 2)]
        assert values == sorted(values)

    def test_stays_inside_zero_and_one_at_the_clamp_limits(self):
        widest = irt.PARAMETER_MAX - irt.PARAMETER_MIN
        assert 0.0 < irt.probability_correct(-widest, 0.0)
        assert irt.probability_correct(widest, 0.0) < 1.0


class TestItemLearningRate:
    """The decaying step size for item difficulty."""

    def test_starts_at_the_base_rate(self):
        assert irt.item_learning_rate(0) == pytest.approx(
            irt.ITEM_BASE_LEARNING_RATE
        )

    def test_halves_after_one_half_life(self):
        n = int(irt.ITEM_RATE_HALF_LIFE)
        assert irt.item_learning_rate(n) == pytest.approx(
            irt.ITEM_BASE_LEARNING_RATE / 2
        )

    def test_decreases_monotonically(self):
        rates = [irt.item_learning_rate(n) for n in range(0, 100, 5)]
        assert rates == sorted(rates, reverse=True)

    def test_tends_to_zero_so_difficulty_converges(self):
        assert irt.item_learning_rate(100_000) < 1e-3

    def test_never_reaches_zero_or_goes_negative(self):
        assert irt.item_learning_rate(10**9) > 0.0


class TestApplyAnswerDirection:
    """Which way each parameter moves."""

    def test_correct_answer_raises_ability_and_lowers_difficulty(self):
        u = irt.apply_answer(
            theta=0.0, difficulty=0.0, times_answered=0, is_correct=True
        )
        assert u.theta_after > u.theta_before
        assert u.b_after < u.b_before

    def test_wrong_answer_lowers_ability_and_raises_difficulty(self):
        u = irt.apply_answer(
            theta=0.0, difficulty=0.0, times_answered=0, is_correct=False
        )
        assert u.theta_after < u.theta_before
        assert u.b_after > u.b_before

    def test_parameters_always_move_in_opposite_directions(self):
        for theta in (-2.0, 0.0, 1.5):
            for correct in (True, False):
                u = irt.apply_answer(
                    theta=theta,
                    difficulty=0.5,
                    times_answered=3,
                    is_correct=correct,
                )
                theta_move = u.theta_after - u.theta_before
                b_move = u.b_after - u.b_before
                assert theta_move * b_move < 0


class TestApplyAnswerMagnitude:
    """How far each parameter moves, and why."""

    def test_matched_question_moves_ability_by_half_the_rate(self):
        u = irt.apply_answer(
            theta=0.0, difficulty=0.0, times_answered=0, is_correct=True
        )
        expected = irt.ABILITY_LEARNING_RATE * 0.5
        assert u.theta_after - u.theta_before == pytest.approx(expected)

    def test_a_surprising_result_moves_more_than_an_expected_one(self):
        """A weak student beating a hard question is strong evidence."""
        surprising = irt.apply_answer(
            theta=-2.0, difficulty=2.0, times_answered=0, is_correct=True
        )
        expected = irt.apply_answer(
            theta=2.0, difficulty=-2.0, times_answered=0, is_correct=True
        )
        assert (
            surprising.theta_after - surprising.theta_before
            > expected.theta_after - expected.theta_before
        )

    def test_a_well_calibrated_item_moves_less_than_a_new_one(self):
        new = irt.apply_answer(
            theta=0.0, difficulty=0.0, times_answered=0, is_correct=True
        )
        seasoned = irt.apply_answer(
            theta=0.0, difficulty=0.0, times_answered=200, is_correct=True
        )
        assert abs(seasoned.b_after - seasoned.b_before) < abs(
            new.b_after - new.b_before
        )

    def test_a_single_step_cannot_exceed_its_learning_rate(self):
        u = irt.apply_answer(
            theta=-3.9, difficulty=3.9, times_answered=0, is_correct=True
        )
        assert abs(u.theta_after - u.theta_before) <= irt.ABILITY_LEARNING_RATE

    def test_reports_the_rates_it_actually_used(self):
        u = irt.apply_answer(
            theta=0.0, difficulty=0.0, times_answered=10, is_correct=True
        )
        assert u.k_theta == irt.ABILITY_LEARNING_RATE
        assert u.k_b == pytest.approx(irt.item_learning_rate(10))


class TestClamping:
    """Parameters stay inside the representable range."""

    def test_ability_cannot_climb_past_the_ceiling(self):
        u = irt.apply_answer(
            theta=irt.PARAMETER_MAX,
            difficulty=-4.0,
            times_answered=0,
            is_correct=True,
        )
        assert u.theta_after == irt.PARAMETER_MAX

    def test_ability_cannot_fall_past_the_floor(self):
        u = irt.apply_answer(
            theta=irt.PARAMETER_MIN,
            difficulty=4.0,
            times_answered=0,
            is_correct=False,
        )
        assert u.theta_after == irt.PARAMETER_MIN

    def test_difficulty_cannot_fall_past_the_floor(self):
        u = irt.apply_answer(
            theta=4.0,
            difficulty=irt.PARAMETER_MIN,
            times_answered=0,
            is_correct=True,
        )
        assert u.b_after == irt.PARAMETER_MIN

    def test_updates_self_limit_so_play_never_reaches_the_ceiling(self):
        """The clamp is a guard, not a destination.

        As theta climbs above b, p approaches 1 and the error term
        collapses, so each step is smaller than the last. 500 consecutive
        correct answers on the easiest possible question still leave theta
        far short of the ceiling — the clamp only matters as protection
        against pathological input, never as normal behaviour.
        """
        theta = 0.0
        steps = []
        for _ in range(500):
            u = irt.apply_answer(
                theta=theta,
                difficulty=irt.PARAMETER_MIN,
                times_answered=0,
                is_correct=True,
            )
            steps.append(u.theta_after - u.theta_before)
            theta = u.theta_after

        assert theta < irt.PARAMETER_MAX
        assert steps == sorted(steps, reverse=True)
        assert steps[-1] < steps[0] / 2


class TestReplay:
    """An attempt row must be reconstructable from what it stores.

    This is what makes the attempts table auditable: p_correct is not
    stored, so a replay recomputes it from theta_before and b_before.
    """

    @pytest.mark.parametrize("correct", [True, False])
    @pytest.mark.parametrize(
        "theta, difficulty", [(0.0, 0.0), (-1.5, 0.5), (2.0, -1.0)]
    )
    def test_stored_fields_reproduce_the_update(
        self, theta, difficulty, correct
    ):
        u = irt.apply_answer(
            theta=theta,
            difficulty=difficulty,
            times_answered=7,
            is_correct=correct,
        )

        p = 1.0 / (1.0 + math.exp(-(u.theta_before - u.b_before)))
        error = (1.0 if correct else 0.0) - p

        assert u.theta_after == pytest.approx(
            irt.clamp(u.theta_before + u.k_theta * error)
        )
        assert u.b_after == pytest.approx(irt.clamp(u.b_before - u.k_b * error))

    def test_raw_arithmetic_fails_at_the_boundary_without_the_clamp(self):
        """The trap flagged in Phase 1.

        At the limits a clamped update does not satisfy the unclamped
        identity. A replay check that forgets to clamp reports a false
        failure, so this pins the behaviour rather than leaving it to be
        rediscovered.
        """
        u = irt.apply_answer(
            theta=irt.PARAMETER_MAX,
            difficulty=-4.0,
            times_answered=0,
            is_correct=True,
        )
        error = 1.0 - u.p_correct
        unclamped = u.theta_before + u.k_theta * error

        assert unclamped > irt.PARAMETER_MAX
        assert u.theta_after != pytest.approx(unclamped)
        assert u.theta_after == pytest.approx(irt.clamp(unclamped))


class TestConvergence:
    """The rule has to behave over a whole session, not just one answer."""

    def test_ability_converges_toward_a_simulated_true_level(self):
        """Recovers a simulated student's true ability from their answers.

        A constant step size never freezes, so theta does not converge to
        a point — it settles into a distribution centred on the truth and
        keeps wandering. Averaging across seeds tests the centre; a single
        run can sit anywhere in roughly a +/- 0.35 band, which is the
        price paid for tracking a student who is still learning.
        """
        true_theta = 1.0
        difficulty = 0.0
        p_true = irt.probability_correct(true_theta, difficulty)

        run_means = []
        for seed in range(8):
            rng = random.Random(seed)
            theta = 0.0
            history = []
            for _ in range(600):
                theta = irt.apply_answer(
                    theta=theta,
                    difficulty=difficulty,
                    times_answered=0,
                    is_correct=rng.random() < p_true,
                ).theta_after
                history.append(theta)
            tail = history[-300:]
            run_means.append(sum(tail) / len(tail))

        centre = sum(run_means) / len(run_means)
        assert centre == pytest.approx(true_theta, abs=0.15)

    def test_difficulty_settles_as_answers_accumulate(self):
        """Later answers move b less, so successive changes shrink."""
        moves = []
        difficulty = 0.0
        for n in range(0, 60):
            u = irt.apply_answer(
                theta=0.0,
                difficulty=difficulty,
                times_answered=n,
                is_correct=True,
            )
            moves.append(abs(u.b_after - u.b_before))
            difficulty = u.b_after
        assert moves[-1] < moves[0]
        assert moves == sorted(moves, reverse=True)
