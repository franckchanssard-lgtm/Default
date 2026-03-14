"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { QUESTIONS, DIMENSIONS } from "@/lib/questionnaire";

const LIKERT_OPTIONS = [
  { value: 1, label: "Strongly Disagree" },
  { value: 2, label: "Disagree" },
  { value: 3, label: "Neutral" },
  { value: 4, label: "Agree" },
  { value: 5, label: "Strongly Agree" },
];

export default function SurveyPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showValidation, setShowValidation] = useState(false);
  const [validId, setValidId] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`/api/responses/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Not found");
        return res.json();
      })
      .then(() => setValidId(true))
      .catch(() => setValidId(false));
  }, [id]);

  const answeredCount = Object.keys(answers).length;
  const totalCount = QUESTIONS.length;

  const handleAnswer = (questionId: string, value: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (answeredCount < totalCount) {
      setShowValidation(true);
      setError(`Please answer all ${totalCount} questions.`);
      // Scroll to first unanswered
      const firstUnanswered = QUESTIONS.find((q) => answers[q.id] === undefined);
      if (firstUnanswered) {
        document
          .getElementById(`q-${firstUnanswered.id}`)
          ?.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`/api/responses/${id}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to save answers");
      }

      router.push(`/results/${id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
      setLoading(false);
    }
  };

  if (validId === null) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading survey...</p>
      </main>
    );
  }

  if (validId === false) {
    return (
      <main className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center max-w-md">
          <h1 className="text-xl font-bold mb-2">Survey Not Found</h1>
          <p className="text-gray-500 mb-4">
            This survey link is invalid or has expired.
          </p>
          <Link
            href="/"
            className="text-[var(--primary)] hover:underline font-medium"
          >
            Start a new survey
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-[var(--primary)] bg-[var(--primary)]/10 rounded-full px-4 py-1.5">
              Step 2 of 3
            </div>
            <div className="text-sm text-gray-500">
              {answeredCount}/{totalCount} answered
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
            <div
              className="h-2 rounded-full transition-all duration-300"
              style={{
                width: `${(answeredCount / totalCount) * 100}%`,
                backgroundColor: "var(--primary)",
              }}
            />
          </div>
        </div>

        {/* Questions */}
        <form onSubmit={handleSubmit}>
          {DIMENSIONS.map((dim) => {
            const dimQuestions = QUESTIONS.filter((q) => q.dimension === dim);
            return (
              <div key={dim} className="mb-8">
                <h2 className="text-lg font-semibold mb-4 text-[var(--primary)]">
                  {dim}
                </h2>

                {dimQuestions.map((q) => {
                  const unanswered =
                    showValidation && answers[q.id] === undefined;
                  return (
                    <div
                      key={q.id}
                      id={`q-${q.id}`}
                      className={`bg-white rounded-xl shadow-sm p-5 mb-3 border-2 transition-colors ${
                        unanswered
                          ? "border-red-400"
                          : answers[q.id] !== undefined
                          ? "border-green-200"
                          : "border-transparent"
                      }`}
                    >
                      <p className="text-sm font-medium mb-3">
                        <span className="text-gray-400 mr-2">{q.id}.</span>
                        {q.text}
                        {q.isGating && (
                          <span className="ml-2 text-xs bg-amber-100 text-amber-700 rounded px-1.5 py-0.5">
                            Key question
                          </span>
                        )}
                      </p>

                      <div className="flex flex-wrap gap-2">
                        {LIKERT_OPTIONS.map((opt) => (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() => handleAnswer(q.id, opt.value)}
                            className={`flex-1 min-w-[60px] text-xs py-2 px-1 rounded-lg border transition-all cursor-pointer ${
                              answers[q.id] === opt.value
                                ? "bg-[var(--primary)] text-white border-[var(--primary)]"
                                : "bg-gray-50 text-gray-600 border-gray-200 hover:border-[var(--primary)] hover:text-[var(--primary)]"
                            }`}
                          >
                            <div className="font-bold">{opt.value}</div>
                            <div className="hidden sm:block mt-0.5">
                              {opt.label}
                            </div>
                          </button>
                        ))}
                      </div>

                      {unanswered && (
                        <p className="text-red-500 text-xs mt-2">
                          Please answer this question.
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              href="/"
              className="sm:w-auto bg-white border border-gray-300 text-gray-700 font-medium py-3 px-6 rounded-lg text-center hover:bg-gray-50 transition-colors"
            >
              ← Back
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-[var(--primary)] hover:bg-[var(--primary-dark)] text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Submitting..." : "Submit & View Results →"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
