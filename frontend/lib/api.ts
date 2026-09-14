/**
 * Typed wrappers for the five endpoints in docs/api.md.
 *
 * Every function either resolves with the parsed payload or throws an
 * ApiError. Plain fetch resolves on a 404, and a user id remembered from an
 * earlier visit can go stale, so that case has to be distinguishable from
 * success by status rather than by inspecting the body.
 */

import type {
  AnswerResult,
  NextQuestion,
  Progress,
  Topic,
  User,
} from "./types";

/**
 * Inlined at build time, so the deployed value is set when the frontend is
 * built rather than when it is served. Unset means the local backend.
 */
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  /**
   * @param status The HTTP status, or 0 when the request never got a
   *   response — the backend is down, or the origin is not allowed.
   */
  constructor(
    readonly status: number,
    message: string,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = "ApiError";
  }
}

interface ValidationIssue {
  msg: string;
}

/**
 * Reads FastAPI's error body. A raised HTTPException carries a string
 * `detail`; a validation failure carries a list of issues instead.
 */
async function detailOf(response: Response): Promise<string> {
  try {
    const body: { detail?: string | ValidationIssue[] } = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((issue) => issue.msg).join("; ");
    }
  } catch {
    // Not JSON: fall through to the status line.
  }
  return response.statusText || `HTTP ${response.status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, init);
  } catch (cause) {
    throw new ApiError(0, `could not reach the API at ${BASE_URL}`, {
      cause,
    });
  }
  if (!response.ok) {
    throw new ApiError(response.status, await detailOf(response));
  }
  return (await response.json()) as T;
}

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function listTopics(): Promise<Topic[]> {
  return request("/topics");
}

export function createUser(displayName: string): Promise<User> {
  return post("/users", { displayName });
}

export interface NextQuestionOptions {
  /** Narrows the pool to questions carrying any of these concepts. */
  tags?: readonly string[];
  /** Question ids already asked this session; never served again. */
  exclude?: readonly number[];
}

/**
 * `complete` means nothing is left after the narrowing: the topic, the
 * concepts, or this session's pool. It does not mean the topic is
 * mastered; progress says that.
 */
export function nextQuestion(
  userId: number,
  topicId: number,
  { tags = [], exclude = [] }: NextQuestionOptions = {},
): Promise<NextQuestion> {
  const query = new URLSearchParams({
    userId: String(userId),
    topicId: String(topicId),
  });
  for (const tag of tags) query.append("tag", tag);
  for (const id of exclude) query.append("exclude", String(id));
  return request(`/next-question?${query}`);
}

export function submitAnswer(answer: {
  userId: number;
  questionId: number;
  selectedOptionId: number;
}): Promise<AnswerResult> {
  return post("/submit-answer", answer);
}

export function getProgress(userId: number): Promise<Progress> {
  return request(`/progress/${userId}`);
}
