"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    company_name: "",
    project_name: "",
    go_live_date: "",
    respondent_role: "",
    respondent_email: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.company_name.trim() || !form.project_name.trim()) {
      setError("Company name and project name are required.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const trimmedForm = {
        company_name: form.company_name.trim(),
        project_name: form.project_name.trim(),
        go_live_date: form.go_live_date,
        respondent_role: form.respondent_role.trim(),
        respondent_email: form.respondent_email.trim(),
      };

      const res = await fetch("/api/responses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(trimmedForm),
      });

      if (!res.ok) {
        throw new Error("Failed to create survey");
      }

      const { id } = await res.json();
      router.push(`/survey/${id}`);
    } catch {
      setError("Something went wrong. Please try again.");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-xl">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          {/* Header */}
          <div className="mb-8 text-center">
            <div className="inline-flex items-center gap-2 mb-4 text-sm font-medium text-[var(--primary)] bg-[var(--primary)]/10 rounded-full px-4 py-1.5">
              Step 1 of 3
            </div>
            <h1 className="text-3xl font-bold mb-2">
              Change Readiness Survey
            </h1>
            <p className="text-gray-500">
              Assess your organization&apos;s readiness for a Pigment
              implementation. This survey takes about 5–7 minutes.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Company Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={form.company_name}
                onChange={(e) =>
                  setForm({ ...form, company_name: e.target.value })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
                placeholder="Acme Corp"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Project Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={form.project_name}
                onChange={(e) =>
                  setForm({ ...form, project_name: e.target.value })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
                placeholder="FP&A Transformation"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Go-live Date{" "}
                <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <input
                type="date"
                value={form.go_live_date}
                onChange={(e) =>
                  setForm({ ...form, go_live_date: e.target.value })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Your Role{" "}
                <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <input
                type="text"
                value={form.respondent_role}
                onChange={(e) =>
                  setForm({ ...form, respondent_role: e.target.value })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
                placeholder="Project Manager"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Email{" "}
                <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <input
                type="email"
                value={form.respondent_email}
                onChange={(e) =>
                  setForm({ ...form, respondent_email: e.target.value })
                }
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
                placeholder="you@company.com"
              />
            </div>

            {error && <p className="text-red-500 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[var(--primary)] hover:bg-[var(--primary-dark)] text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Creating survey..." : "Start Survey →"}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          No data is shared externally. Results are accessible via a unique URL.
        </p>
      </div>
    </main>
  );
}
