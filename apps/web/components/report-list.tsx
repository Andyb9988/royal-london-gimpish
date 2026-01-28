import { ReportCard } from "@/components/report-card";
import { EmptyState } from "@/components/empty-state";
import type { Report } from "@/lib/api/types";

export function ReportList({
  reports,
  hrefPrefix,
}: {
  reports: Report[];
  hrefPrefix: string;
}) {
  if (!reports.length) {
    return (
      <EmptyState
        title="No reports yet"
        description="Create a match report to kick things off."
      />
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {reports.map((report) => (
        <ReportCard
          key={report.id}
          report={report}
          href={`${hrefPrefix}/${report.id}`}
        />
      ))}
    </div>
  );
}
