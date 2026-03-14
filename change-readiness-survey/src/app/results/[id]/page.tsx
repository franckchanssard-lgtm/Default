"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { SurveyResults, Answers, ResponseRecord } from "@/lib/types";
import { QUESTIONS } from "@/lib/questionnaire";

interface ApiResponse extends ResponseRecord {
  answers: Answers;
  scores: SurveyResults | null;
}

function trafficLightColor(tl: "red" | "orange" | "green"): string {
  switch (tl) {
    case "red":
      return "var(--red)";
    case "orange":
      return "var(--orange)";
    case "green":
      return "var(--green)";
  }
}

function trafficLightBg(tl: "red" | "orange" | "green"): string {
  switch (tl) {
    case "red":
      return "#fef2f2";
    case "orange":
      return "#fffbeb";
    case "green":
      return "#f0fdf4";
  }
}

function trafficLightLabel(tl: "red" | "orange" | "green"): string {
  switch (tl) {
    case "red":
      return "High Risk";
    case "orange":
      return "Moderate";
    case "green":
      return "On Track";
  }
}

export default function ResultsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`/api/responses/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Not found");
        return res.json();
      })
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => {
        setError("Survey not found or not yet completed.");
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading results...</p>
      </main>
    );
  }

  if (error || !data || !data.scores) {
    return (
      <main className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center max-w-md">
          <h1 className="text-xl font-bold mb-2">No Results</h1>
          <p className="text-gray-500 mb-4">
            {error || "This survey has not been completed yet."}
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

  const { scores } = data;

  return (
    <main className="min-h-screen py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-medium text-[var(--primary)] bg-[var(--primary)]/10 rounded-full px-4 py-1.5">
              Step 3 of 3 — Results
            </div>
          </div>
          <h1 className="text-2xl font-bold mb-1">
            {data.company_name} — {data.project_name}
          </h1>
          <p className="text-gray-400 text-sm">
            Submitted {new Date(data.created_at).toLocaleDateString()}
            {data.respondent_role && ` · ${data.respondent_role}`}
          </p>
        </div>

        {/* Overall Score */}
        <div
          className="rounded-2xl shadow-lg p-6 mb-6 text-center"
          style={{
            backgroundColor: trafficLightBg(scores.overallTrafficLight),
          }}
        >
          <p className="text-sm font-medium text-gray-500 mb-2">
            Overall Readiness Score
          </p>
          <div
            className="text-6xl font-bold mb-2"
            style={{ color: trafficLightColor(scores.overallTrafficLight) }}
          >
            {scores.overall}
          </div>
          <div
            className="inline-block text-sm font-semibold px-3 py-1 rounded-full text-white"
            style={{
              backgroundColor: trafficLightColor(scores.overallTrafficLight),
            }}
          >
            {trafficLightLabel(scores.overallTrafficLight)}
          </div>
        </div>

        {/* Dimension Scores */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Scores by Dimension</h2>
          <div className="space-y-4">
            {scores.dimensions.map((dim) => (
              <div key={dim.dimension}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium">{dim.dimension}</span>
                  <span
                    className="font-bold"
                    style={{ color: trafficLightColor(dim.trafficLight) }}
                  >
                    {dim.score}/100
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-4 rounded-full transition-all duration-500"
                    style={{
                      width: `${dim.score}%`,
                      backgroundColor: trafficLightColor(dim.trafficLight),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Gating Warnings */}
        {scores.gatingWarnings.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 mb-6">
            <h2 className="text-lg font-semibold mb-3 text-red-700">
              Gating Risks
            </h2>
            <ul className="space-y-2">
              {scores.gatingWarnings.map((w, i) => (
                <li key={i} className="text-sm text-red-600 flex items-start gap-2">
                  <span className="mt-0.5">&#9888;</span>
                  <span>{w}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Top Risks */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-3">Top Risks</h2>
          <ul className="space-y-2">
            {scores.risks.map((r, i) => (
              <li
                key={i}
                className="text-sm text-gray-700 flex items-start gap-2"
              >
                <span className="text-red-400 mt-0.5">●</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Recommendations */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-3">
            Recommended Next Actions
          </h2>
          <ul className="space-y-2">
            {scores.recommendations.map((r, i) => (
              <li
                key={i}
                className="text-sm text-gray-700 flex items-start gap-2"
              >
                <span className="text-[var(--primary)] mt-0.5">→</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Answer Detail */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-3">Your Answers</h2>
          <div className="space-y-2">
            {QUESTIONS.map((q) => {
              const val = data.answers[q.id];
              const isLow = val !== undefined && val <= 2;
              return (
                <div
                  key={q.id}
                  className={`flex items-center justify-between text-sm py-1.5 border-b border-gray-100 ${
                    isLow ? "text-red-600" : "text-gray-700"
                  }`}
                >
                  <span className="flex-1 pr-4">
                    <span className="text-gray-400 mr-1">{q.id}.</span>
                    {q.text}
                  </span>
                  <span className="font-bold whitespace-nowrap">
                    {val !== undefined ? `${val}/5` : "—"}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <a
            href={`/api/responses/${id}/export.csv`}
            className="flex-1 bg-white border border-gray-300 text-gray-700 font-medium py-3 rounded-lg text-center hover:bg-gray-50 transition-colors"
          >
            Export CSV
          </a>
          <Link
            href="/"
            className="flex-1 bg-[var(--primary)] hover:bg-[var(--primary-dark)] text-white font-medium py-3 rounded-lg text-center transition-colors"
          >
            Start a New Survey
          </Link>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Share this page&apos;s URL to give others access to these results.
        </p>
      </div>
    </main>
  );
}
