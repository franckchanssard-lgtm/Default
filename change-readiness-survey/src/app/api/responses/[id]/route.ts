import { NextRequest, NextResponse } from "next/server";
import { getResponse } from "@/lib/db";
import { computeScores } from "@/lib/scoring";
import { QUESTIONS } from "@/lib/questionnaire";
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

    return NextResponse.json({
      ...response,
      answers,
      scores,
    });
  } catch (error) {
    console.error("Error fetching response:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
