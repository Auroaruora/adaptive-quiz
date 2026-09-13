import { OptionButton } from "./OptionButton";
import type { Option, OptionState } from "@/lib/types";

interface OptionListProps {
  options: Option[];
  /** Null until the student answers. */
  chosenOptionId: number | null;
  /** Null while the question is still being asked. */
  correctOptionId: number | null;
  onSelect?: (optionId: number) => void;
}

/**
 * Decides how each option looks once an answer is in.
 *
 * All four stay on screen. The student's choice and the right answer are
 * both marked, and the two that are neither recede rather than
 * disappearing, so the choice is still readable in context.
 */
function stateFor(
  option: Option,
  chosenOptionId: number | null,
  correctOptionId: number | null,
): OptionState {
  if (correctOptionId === null) {
    return option.id === chosenOptionId ? "selected" : "idle";
  }
  if (option.id === correctOptionId) return "correct";
  if (option.id === chosenOptionId) return "incorrect";
  return "muted";
}

export function OptionList({
  options,
  chosenOptionId,
  correctOptionId,
  onSelect,
}: OptionListProps) {
  return (
    <ul className="flex list-none flex-col gap-3">
      {options.map((option) => (
        <li key={option.id}>
          <OptionButton
            option={option}
            state={stateFor(option, chosenOptionId, correctOptionId)}
            onSelect={onSelect}
          />
        </li>
      ))}
    </ul>
  );
}
