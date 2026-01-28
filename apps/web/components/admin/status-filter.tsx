"use client";

import { cn } from "@/lib/utils";
import type { ReportStatus } from "@/lib/api/types";

const options: { label: string; value: ReportStatus | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Drafts", value: "draft" },
  { label: "Processing", value: "processing" },
  { label: "Published", value: "published" },
  { label: "Failed", value: "failed" },
];

export function StatusFilter({
  value,
  onChange,
}: {
  value: ReportStatus | "all";
  onChange: (value: ReportStatus | "all") => void;
}) {
  return (
    <div className="inline-flex rounded-full border border-slate-200 bg-white p-1">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className={cn(
            "rounded-full px-4 py-1 text-sm transition",
            value === option.value
              ? "bg-ink text-white"
              : "text-slate-600 hover:bg-slate-100",
          )}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
