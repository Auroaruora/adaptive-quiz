"""Loads hand-authored question content from seeds/*.yaml into MySQL.

Every file is validated in full before anything is written, and the whole
load runs in one transaction, so a malformed question cannot leave the
database half-seeded.

Usage:
    python scripts/seed.py            # insert new questions, skip existing
    python scripts/seed.py --reset    # delete all questions first
"""

import argparse
import hashlib
import pathlib
import random
import re
import sys

import yaml
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.config import database_url  # noqa: E402
from app.db.models import (  # noqa: E402
    LABEL_TO_INITIAL_B,
    Attempt,
    DifficultyLabel,
    Question,
    QuestionOption,
    QuestionStep,
    QuestionTag,
    Tag,
    Topic,
)

#: Tags must be lowercase, hyphen-separated slugs. Enforced so a typo
#: becomes a new tag silently shared with nothing, which is exactly the
#: isolation the tag system exists to avoid.
_TAG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

_SEEDS_DIR = pathlib.Path(__file__).resolve().parents[1] / "seeds"


def _validate(path: pathlib.Path, data: dict) -> list[str]:
    """Checks one seed file against every rule the schema enforces.

    Catching these here turns an opaque IntegrityError from MySQL into a
    message naming the file and question.

    Args:
        path: Seed file the data came from, used in messages.
        data: Parsed YAML contents.

    Returns:
        Human-readable problems, empty when the file is valid.
    """
    problems: list[str] = []
    where = path.name

    topic = data.get("topic") or {}
    for field in ("slug", "name"):
        if not topic.get(field):
            problems.append(f"{where}: topic is missing {field}")

    questions = data.get("questions") or []
    if not questions:
        problems.append(f"{where}: no questions")

    seen_stems: set[str] = set()
    for i, q in enumerate(questions, 1):
        at = f"{where} Q{i}"
        stem = (q.get("stem") or "").strip()
        if not stem:
            problems.append(f"{at}: empty stem")
        elif len(stem) > 1000:
            problems.append(f"{at}: stem exceeds 1000 characters")
        elif stem in seen_stems:
            problems.append(f"{at}: duplicate stem within the file")
        else:
            seen_stems.add(stem)

        label = q.get("difficulty")
        if label not in {m.value for m in DifficultyLabel}:
            problems.append(f"{at}: bad difficulty {label!r}")

        tags = q.get("tags") or []
        # Two minimum: a question whose only tag is unique is as isolated
        # as one with no tags, which defeats the point.
        if len(tags) < 2:
            problems.append(f"{at}: needs at least 2 tags, has {len(tags)}")
        if len(set(tags)) != len(tags):
            problems.append(f"{at}: duplicate tag")
        for tag in tags:
            if not isinstance(tag, str) or not _TAG_PATTERN.fullmatch(tag):
                problems.append(f"{at}: bad tag {tag!r}")

        steps = q.get("solution") or []
        if len(steps) < 2:
            problems.append(f"{at}: needs at least 2 solution steps")
        for step in steps:
            if not step or not step.strip():
                problems.append(f"{at}: empty solution step")
            elif len(step) > 500:
                problems.append(f"{at}: solution step exceeds 500 characters")

        options = q.get("options") or []
        if len(options) != 4:
            problems.append(f"{at}: {len(options)} options, expected 4")

        correct = [o for o in options if o.get("correct")]
        if len(correct) != 1:
            problems.append(
                f"{at}: {len(correct)} correct options, expected exactly 1"
            )

        texts = [(o.get("text") or "").strip() for o in options]
        if any(not t for t in texts):
            problems.append(f"{at}: an option has empty text")
        if len(set(texts)) != len(texts):
            problems.append(f"{at}: duplicate option text")

        for o in options:
            note = o.get("misconception")
            if o.get("correct"):
                if note:
                    problems.append(
                        f"{at}: the correct option carries a misconception"
                    )
            elif not note or not note.strip():
                problems.append(
                    f"{at}: wrong option {o.get('text')!r} has no misconception"
                )
            elif len(note) > 500:
                problems.append(f"{at}: misconception exceeds 500 characters")

    return problems


def _ordered_options(stem: str, options: list[dict]) -> list[dict]:
    """Shuffles a question's options into their display order.

    The RNG is seeded from the stem rather than globally, so each
    question's order is reproducible and unaffected by adding, removing,
    or reordering other questions in the file.

    Args:
        stem: Question text, used as the shuffle seed.
        options: Options in authored order.

    Returns:
        The same options in display order.
    """
    digest = hashlib.sha256(stem.encode("utf-8")).hexdigest()
    rng = random.Random(int(digest[:16], 16))
    shuffled = list(options)
    rng.shuffle(shuffled)
    return shuffled


def _tag(session: Session, slug: str, cache: dict[str, Tag]) -> Tag:
    """Fetches a tag by slug, creating it on first use.

    Args:
        session: Open session; the caller owns the transaction.
        slug: Tag slug from a seed file.
        cache: Tags already seen this run, to avoid a query per question.

    Returns:
        The tag row.
    """
    if slug in cache:
        return cache[slug]
    tag = session.scalar(select(Tag).where(Tag.slug == slug))
    if tag is None:
        tag = Tag(slug=slug, name=slug.replace("-", " ").capitalize())
        session.add(tag)
        session.flush()
    cache[slug] = tag
    return tag


def _load_file(
    session: Session, path: pathlib.Path, tag_cache: dict[str, Tag]
) -> tuple[int, int]:
    """Loads one seed file, skipping questions already present.

    Args:
        session: Open session; the caller owns the transaction.
        path: Seed file to load.
        tag_cache: Tags already created this run, shared across files so
            a tag used in two topics is created once.

    Returns:
        Counts of questions inserted and skipped.
    """
    data = yaml.safe_load(path.read_text())
    spec = data["topic"]

    topic = session.scalar(select(Topic).where(Topic.slug == spec["slug"]))
    if topic is None:
        topic = Topic(
            slug=spec["slug"],
            name=spec["name"],
            description=spec.get("description"),
        )
        session.add(topic)
        session.flush()

    existing = set(
        session.scalars(
            select(Question.stem).where(Question.topic_id == topic.id)
        )
    )

    inserted = skipped = 0
    for q in data["questions"]:
        stem = q["stem"].strip()
        if stem in existing:
            skipped += 1
            continue

        label = DifficultyLabel(q["difficulty"])
        question = Question(
            topic_id=topic.id,
            stem=stem,
            difficulty_label=label,
            difficulty_b=LABEL_TO_INITIAL_B[label],
        )
        session.add(question)
        session.flush()

        for position, option in enumerate(
            _ordered_options(stem, q["options"]), 1
        ):
            session.add(
                QuestionOption(
                    question_id=question.id,
                    option_text=option["text"].strip(),
                    is_correct=bool(option.get("correct")),
                    position=position,
                    misconception=(
                        None
                        if option.get("correct")
                        else " ".join(option["misconception"].split())
                    ),
                )
            )

        for slug in q["tags"]:
            session.add(
                QuestionTag(
                    question_id=question.id,
                    tag_id=_tag(session, slug, tag_cache).id,
                )
            )

        for number, step in enumerate(q["solution"], 1):
            session.add(
                QuestionStep(
                    question_id=question.id,
                    step_number=number,
                    body=" ".join(step.split()),
                )
            )

        inserted += 1

    return inserted, skipped


def _isolated(session: Session) -> list[str]:
    """Finds questions sharing no tag with any other in their topic.

    The two-tag rule in `_validate` checks the letter; this checks what
    the rule is for. A question can carry two tags and still be isolated
    if both are unique to it, and similarity only ever counts tags two
    questions *share* — so such a question can never be offered as
    practice for anything, which is the one failure the tag system exists
    to prevent.

    Args:
        session: Open session; the caller owns the transaction.

    Returns:
        Descriptions of isolated questions, empty when all are connected.
    """
    rows = session.execute(
        select(Question.id, Question.topic_id, Question.stem, Tag.slug)
        .join(QuestionTag, QuestionTag.question_id == Question.id)
        .join(Tag, Tag.id == QuestionTag.tag_id)
    ).all()

    tags: dict[int, set[str]] = {}
    topic: dict[int, int] = {}
    stem: dict[int, str] = {}
    for question_id, topic_id, text, slug in rows:
        tags.setdefault(question_id, set()).add(slug)
        topic[question_id] = topic_id
        stem[question_id] = text

    lonely = []
    for question_id, own in tags.items():
        if not any(
            own & other
            for peer, other in tags.items()
            if peer != question_id and topic[peer] == topic[question_id]
        ):
            lonely.append(f"{stem[question_id][:60]!r} shares no tag")
    return lonely


def _reset(session: Session) -> int:
    """Deletes all question content, refusing if any attempt references it.

    Options and steps cascade from their question. Topics are left alone,
    since deleting one would cascade into per-student ability rows.

    Args:
        session: Open session; the caller owns the transaction.

    Returns:
        Number of questions deleted.

    Raises:
        SystemExit: If attempts exist, since answered questions are
            protected by ON DELETE RESTRICT and the delete would fail.
    """
    attempts = session.scalar(select(func.count()).select_from(Attempt))
    if attempts:
        sys.exit(
            f"refusing to reset: {attempts} attempt(s) reference these "
            "questions. Clearing them would destroy answer history."
        )

    questions = session.scalars(select(Question)).all()
    for question in questions:
        session.delete(question)
    return len(questions)


def main() -> None:
    """Validates every seed file, then loads them in one transaction."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete existing questions before loading",
    )
    args = parser.parse_args()

    paths = sorted(_SEEDS_DIR.glob("*.yaml"))
    if not paths:
        sys.exit(f"no seed files found in {_SEEDS_DIR}")

    problems: list[str] = []
    for path in paths:
        problems.extend(_validate(path, yaml.safe_load(path.read_text())))
    if problems:
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        sys.exit(f"{len(problems)} problem(s) found; nothing was written")

    engine = create_engine(database_url("pymysql"))
    with Session(engine) as session, session.begin():
        if args.reset:
            print(f"reset: deleted {_reset(session)} question(s)")
        tag_cache: dict[str, Tag] = {}
        for path in paths:
            inserted, skipped = _load_file(session, path, tag_cache)
            print(f"{path.name}: {inserted} inserted, {skipped} skipped")

        lonely = _isolated(session)
        if lonely:
            for item in lonely:
                print(f"  {item}", file=sys.stderr)
            sys.exit(
                f"{len(lonely)} question(s) share no tag with any other in "
                "their topic, so nothing can be offered as practice for "
                "them. Add a broader tag."
            )

    _report(engine)
    engine.dispose()


def _report(engine) -> None:
    """Prints what ended up in the database, per topic.

    Args:
        engine: Engine to open a short reporting session on.
    """
    with Session(engine) as session:
        print()
        for topic in session.scalars(select(Topic).order_by(Topic.slug)):
            counts = {
                label.value: session.scalar(
                    select(func.count())
                    .select_from(Question)
                    .where(
                        Question.topic_id == topic.id,
                        Question.difficulty_label == label,
                    )
                )
                for label in DifficultyLabel
            }
            total = sum(counts.values())
            spread = " / ".join(f"{k} {v}" for k, v in counts.items())
            print(f"{topic.slug:<16} {total:>3} questions   {spread}")

        positions = session.execute(
            select(QuestionOption.position, func.count())
            .where(QuestionOption.is_correct.is_(True))
            .group_by(QuestionOption.position)
            .order_by(QuestionOption.position)
        ).all()
        spread = "  ".join(f"pos {p}: {n}" for p, n in positions)
        print(f"\ncorrect answer positions after shuffle:  {spread}")


if __name__ == "__main__":
    main()
