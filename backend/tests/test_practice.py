"""Tests for mistake decay and spacing.

`now` is passed in everywhere rather than read from the clock, so these
age mistakes by weeks without waiting or patching time.
"""

import datetime

import pytest

from app import practice

NOW = datetime.datetime(2026, 9, 13, 12, 0, 0)


def ago(**kwargs) -> datetime.datetime:
    """A timestamp that far in the past, relative to NOW."""
    return NOW - datetime.timedelta(**kwargs)


class TestRecencyWeight:
    """How much one past mistake still counts."""

    def test_something_that_just_happened_counts_fully(self):
        assert practice.recency_weight(NOW, NOW) == pytest.approx(1.0)

    def test_halves_after_one_half_life(self):
        when = ago(days=practice.MISTAKE_HALF_LIFE_DAYS)
        assert practice.recency_weight(when, NOW) == pytest.approx(0.5)

    def test_quarters_after_two_half_lives(self):
        when = ago(days=practice.MISTAKE_HALF_LIFE_DAYS * 2)
        assert practice.recency_weight(when, NOW) == pytest.approx(0.25)

    def test_decreases_with_age(self):
        weights = [
            practice.recency_weight(ago(days=d), NOW)
            for d in (0, 1, 7, 30, 180)
        ]
        assert weights == sorted(weights, reverse=True)

    def test_fades_but_never_reaches_zero(self):
        assert 0 < practice.recency_weight(ago(days=3650), NOW) < 1e-6

    def test_a_future_timestamp_cannot_exceed_full_weight(self):
        """Clock skew should not let a mistake count more than fully."""
        ahead = NOW + datetime.timedelta(days=5)
        assert practice.recency_weight(ahead, NOW) == pytest.approx(1.0)


class TestUrgency:
    """How hard a question's mistakes pull practice toward it."""

    def test_no_mistakes_means_no_pull(self):
        assert practice.urgency([], NOW) == 0.0

    def test_repeated_mistakes_add_up(self):
        once = practice.urgency([ago(hours=1)], NOW)
        thrice = practice.urgency([ago(hours=1)] * 3, NOW)
        assert thrice > once

    def test_one_recent_mistake_outweighs_several_old_ones(self):
        """The whole point of decaying: January should not win."""
        recent = practice.urgency([ago(hours=2)], NOW)
        ancient = practice.urgency([ago(days=120)] * 5, NOW)
        assert recent > ancient

    def test_the_same_mistakes_matter_less_as_they_age(self):
        fresh = practice.urgency([ago(days=1), ago(days=2)], NOW)
        stale = practice.urgency([ago(days=61), ago(days=62)], NOW)
        assert stale < fresh

    def test_a_question_missed_twice_today_beats_one_missed_once(self):
        twice = practice.urgency([ago(hours=1), ago(hours=3)], NOW)
        once = practice.urgency([ago(hours=2)], NOW)
        assert twice > once
