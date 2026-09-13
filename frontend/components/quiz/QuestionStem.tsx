interface QuestionStemProps {
  children: string;
}

/**
 * The question being asked.
 *
 * Set in sans rather than the math family. Stems mix prose and expressions
 * inline with nothing marking where one ends — "Find the slope of y = x^2
 * at x = 3." — so any rule for detecting the maths would misfire on the
 * prose. Marking it properly is a change to the seed content, not to this
 * component.
 */
export function QuestionStem({ children }: QuestionStemProps) {
  return <h1 className="text-title text-ink">{children}</h1>;
}
