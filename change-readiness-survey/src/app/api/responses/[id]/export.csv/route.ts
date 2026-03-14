import { NextRequest, NextResponse } from "next/server";
import { getResponse } from "@/lib/db";
import { computeScores } from "@/lib/scoring";
import { QUESTIONS, DIMENSIONS } from "@/lib/questionnaire";
import { Answers } from "@/lib/types";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const response = await getResponse(id);

    if (!response) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    const answers: Answers = response.answers_json
      ? JSON.parse(response.answers_json)
      : {};
    const hasAnswers = Object.keys(answers).length === QUESTIONS.length;
    const scores = hasAnswers ? computeScores(answers) : null;

    // Build CSV
    const rows: string[][] = [];

    // Header row
    rows.push(["Field", "Value"]);

    // Context
    rows.push(["Company", response.company_name]);
    rows.push(["Project", response.project_name]);
    rows.push(["Go-live Date", response.go_live_date || ""]);
    rows.push(["Respondent Role", response.respondent_role || ""]);
    rows.push(["Respondent Email", response.respondent_email || ""]);
    rows.push(["Date", response.created_at]);
    rows.push([]);

    // Questions
    rows.push(["Question ID", "Dimension", "Question", "Answer"]);
    for (const q of QUESTIONS) {
      rows.push([
        q.id,
        q.dimension,
        q.text,
        String(answers[q.id] ?? ""),
      ]);
    }
    rows.push([]);

    // Dimension scores
    rows.push(["Dimension", "Score", "Traffic Light"]);
    if (scores) {
      for (const dim of DIMENSIONS) {
        const ds = scores.dimensions.find((d) => d.dimension === dim)!;
        rows.push([dim, String(ds.score), ds.trafficLight]);
      }
      rows.push([]);
      rows.push(["Overall Score", String(scores.overall), scores.overallTrafficLight]);
      rows.push([]);

      // Gating Warnings
      if (scores.gatingWarnings.length > 0) {
        rows.push(["Gating Warnings"]);
        for (const w of scores.gatingWarnings) {
          rows.push([w]);
        }
        rows.push([]);
      }

      // Risks
      if (scores.risks.length > 0) {
        rows.push(["Top Risks"]);
        for (const r of scores.risks) {
          rows.push([r]);
        }
        rows.push([]);
      }

      // Recommendations
      if (scores.recommendations.length > 0) {
        rows.push(["Recommendations"]);
        for (const r of scores.recommendations) {
          rows.push([r]);
        }
      }
    }

    const csv = rows
      .map((row) =>
        row
          .map((cell) => {
            if (cell.includes(",") || cell.includes('"') || cell.includes("\n")) {
              return `"${cell.replace(/"/g, '""')}"`;
            }
            return cell;
          })
          .join(",")
      )
      .join("\n");

    return new NextResponse(csv, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": `attachment; filename="survey-${id}.csv"`,
      },
    });
  } catch (error) {
    console.error("Error exporting CSV:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
