import Link from "next/link";

import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import type { Report } from "@/lib/api/types";

export function ReportCard({
  report,
  href,
}: {
  report: Report;
  href: string;
}) {
  return (
    <Card className="p-6 transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link href={href} className="text-lg font-semibold text-ink">
            {report.opponent ?? "Untitled opponent"}
          </Link>
          <p className="mt-1 text-sm text-muted">
            {new Date(report.date).toLocaleDateString()} · {report.id}
          </p>
        </div>
        <StatusBadge status={report.status} />
      </div>
      {report.content ? (
        <p className="mt-4 text-sm text-slate-600">
          {report.content}
        </p>
      ) : (
        <p className="mt-4 text-sm text-slate-400">
          No content yet. Add the match summary.
        </p>
      )}
    </Card>
  );
}
