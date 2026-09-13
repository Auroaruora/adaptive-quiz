"""How recent mistakes and recent exposure shape what is served next.

Pure functions — no database, no clock. The caller passes `now` in, which
is what makes decay testable without freezing time.

Two ideas, both driven by when things happened rather than how often:

Mistakes decay. Five misses in January should not pull practice as hard
as one miss yesterday, or an early struggle distorts the mix forever.

Questions are spaced. Answering correctly moments after reading the
solution shows you can remember a sentence, not that you learned
anything, so a question just seen is held back.
"""

import datetime
import math
from collections.abc import Iterable

#: Days after which a mistake counts half as much. Two weeks is short
#: enough that a fixed weakness fades once it stops recurring, and long
#: enough to survive a few days away from the app.
MISTAKE_HALF_LIFE_DAYS = 14.0

#: How many of the most recent answers a question must sit outside before
#: it can be served again.
SPACING_WINDOW = 5


def recency_weight(when: datetime.datetime, now: datetime.datetime) -> float:
    """Weighs one past event by how long ago it happened.

    Args:
        when: When the event happened.
        now: The current time, passed in rather than read.

    Returns:
        1.0 for something that just happened, halving every half-life,
        approaching zero but never reaching it. A future timestamp is
        treated as now, so clock skew cannot inflate a weight.
    """
    age_days = max(0.0, (now - when).total_seconds() / 86_400)
    return math.pow(0.5, age_days / MISTAKE_HALF_LIFE_DAYS)


def urgency(
    wrong_at: Iterable[datetime.datetime], now: datetime.datetime
) -> float:
    """How strongly a question's mistakes should pull practice toward it.

    Repeated mistakes add up, so a question missed three times outranks
    one missed once — but only while those misses are recent.

    Args:
        wrong_at: When this question was answered incorrectly.
        now: The current time.

    Returns:
        Zero when there are no mistakes, rising with their number and
        falling with their age.
    """
    return sum(recency_weight(when, now) for when in wrong_at)
