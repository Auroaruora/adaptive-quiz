import { Eyebrow } from "@/components/ui/Eyebrow";
import { Panel } from "@/components/ui/Panel";
import type { AnswerRecord, Progress, Topic } from "@/lib/types";

interface SessionBoardProps {
  mode?: string;
  records: readonly AnswerRecord[];
  /** How many questions the session set out to ask. */
  planned: number;
  progress: Progress;
  onReview: () => void;
  onPractise: (topic: Topic, tags: string[]) => void;
  onSummary: (topic: Topic) => void;
  onBack: () => void;
}

interface Group {
  topic: Topic;
  wrong: AnswerRecord[];
  /** The most specific concept behind each wrong answer, deduplicated. */
  concepts: { slug: string; name: string }[];
}

function groupByTopic(records: readonly AnswerRecord[]): Group[] {
  const groups = new Map<number, Group>();
  for (const record of records) {
    if (record.feedback.isCorrect) continue;
    const group = groups.get(record.topic.id) ?? {
      topic: record.topic,
      wrong: [],
      concepts: [],
    };
    group.wrong.push(record);
    const concept = record.question.tags[0];
    if (concept && !group.concepts.some((c) => c.slug === concept.slug)) {
      group.concepts.push(concept);
    }
    groups.set(record.topic.id, group);
  }
  return [...groups.values()];
}

function optionText(record: AnswerRecord, optionId: number): string {
  return record.question.options.find((o) => o.id === optionId)?.text ?? "—";
}

const SECONDARY =
  "border-line text-ink hover:border-accent hover:text-accent active:bg-accent-soft text-body cursor-pointer rounded-sm border px-6 py-3 font-medium transition-colors";

/**
 * What a session ends on.
 *
 * The number that matters is how many went wrong, so it is the hero. The
 * wrong questions are listed with the answer given and the right one, and
 * every next step starts from them: look at them again, or practise the
 * concepts behind them. A session with nothing wrong says so plainly and
 * offers only the way back.
 */
export function SessionBoard({
  mode,
  records,
  planned,
  progress,
  onReview,
  onPractise,
  onSummary,
  onBack,
}: SessionBoardProps) {
  const wrong = records.filter((r) => !r.feedback.isCorrect).length;
  const groups = groupByTopic(records);
  const ranShort = records.length < planned;

  const finishedTopics = [...new Set(records.map((r) => r.topic))].filter(
    (topic) => {
      const t = progress.topics.find((p) => p.slug === topic.slug);
      return t && t.summary.total > 0 && t.summary.mastered === t.summary.total;
    },
  );

  return (
    <div className="mx-auto flex w-full max-w-[720px] flex-col gap-8">
      <header className="flex flex-col gap-2">
        <p className="text-label text-ink-muted">{mode ?? "Practice"}</p>
        <h1 className="text-h1 text-ink">Session complete</h1>
      </header>

      <Panel tone="deep">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <Eyebrow tone="onDark">How you did</Eyebrow>
            <p className="text-display font-mono">
              {wrong}
              <span className="text-h2 text-surface/60">
                {" / "}
                {records.length}
              </span>
            </p>
            <p className="text-body-lg text-surface/70">
              {wrong === 0
                ? "Nothing wrong. Every answer was right."
                : wrong === 1
                  ? "One question wrong."
                  : `${wrong} questions wrong.`}
              {ranShort &&
                ` Only ${records.length} ${records.length === 1 ? "question was" : "questions were"} available, not ${planned}.`}
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            {wrong > 0 && (
              <button
                type="button"
                onClick={onReview}
                className="bg-surface text-ink hover:bg-accent-soft text-body cursor-pointer rounded-sm px-8 py-4 font-medium transition-colors"
              >
                Go over the {wrong === 1 ? "one" : wrong} you got wrong
              </button>
            )}
            <button
              type="button"
              onClick={onBack}
              className="border-surface/25 text-surface/80 hover:border-surface hover:text-surface text-body cursor-pointer rounded-sm border px-8 py-4 font-medium transition-colors"
            >
              Back to topics
            </button>
          </div>
        </div>
      </Panel>

      {groups.map((group) => (
        <section
          key={group.topic.id}
          className="border-line bg-surface shadow-raised flex flex-col gap-6 rounded-lg border p-6"
        >
          <div className="flex flex-col gap-1">
            <Eyebrow tone="faint">{group.topic.name}</Eyebrow>
            <h2 className="text-h3 text-ink">
              {group.wrong.length === 1
                ? "One to look at again"
                : `${group.wrong.length} to look at again`}
            </h2>
          </div>

          <ol className="flex list-none flex-col gap-4">
            {group.wrong.map((record) => (
              <li
                key={record.question.id}
                className="border-line flex flex-col gap-2 border-t pt-4"
              >
                <p className="text-title text-ink">{record.question.stem}</p>
                <dl className="text-body grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
                  <dt className="text-ink-muted">You answered</dt>
                  <dd className="text-incorrect-ink font-math">
                    {optionText(record, record.chosenOptionId)}
                  </dd>
                  <dt className="text-ink-muted">Correct</dt>
                  <dd className="text-correct-ink font-math">
                    {optionText(record, record.feedback.correctOptionId)}
                  </dd>
                </dl>
              </li>
            ))}
          </ol>

          <div className="flex flex-col gap-3">
            <p className="text-body text-ink-muted">
              Behind these:{" "}
              {group.concepts.map((c, i) => (
                <span key={c.slug} className="text-ink">
                  {i > 0 && ", "}
                  {c.name}
                </span>
              ))}
            </p>
            <button
              type="button"
              onClick={() =>
                onPractise(
                  group.topic,
                  group.concepts.map((c) => c.slug),
                )
              }
              className={`${SECONDARY} self-start`}
            >
              Practise{" "}
              {group.concepts.length === 1 ? "this concept" : "these concepts"}
              {groups.length > 1 && ` in ${group.topic.name}`}
            </button>
          </div>
        </section>
      ))}

      {finishedTopics.map((topic) => (
        <section
          key={topic.id}
          className="border-correct bg-correct-soft flex flex-wrap items-center justify-between gap-4 rounded-lg border p-6"
        >
          <p className="text-body-lg text-correct-ink">
            Every question in {topic.name} has now been answered correctly.
          </p>
          <button
            type="button"
            onClick={() => onSummary(topic)}
            className="border-correct text-correct-ink hover:bg-surface text-body cursor-pointer rounded-sm border px-6 py-3 font-medium transition-colors"
          >
            See the topic summary
          </button>
        </section>
      ))}
    </div>
  );
}
