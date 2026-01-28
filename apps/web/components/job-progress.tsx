import type { Job } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";

const statusStyles: Record<
  Job["status"],
  { label: string; variant: "default" | "success" | "warning" | "error" }
> = {
  queued: { label: "Queued", variant: "default" },
  running: { label: "Running", variant: "warning" },
  succeeded: { label: "Succeeded", variant: "success" },
  failed: { label: "Failed", variant: "error" },
};

export function JobProgress({ jobs }: { jobs: Job[] }) {
  if (!jobs.length) {
    return <p className="text-sm text-muted">No jobs queued yet.</p>;
  }

  return (
    <div className="space-y-3">
      {jobs.map((job) => (
        <div
          key={job.id}
          className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3"
        >
          <div>
            <p className="text-sm font-medium text-ink">
              {job.type.replace(/_/g, " ")}
            </p>
            {job.last_error ? (
              <p className="text-xs text-rose-600">{job.last_error}</p>
            ) : null}
          </div>
          <Badge variant={statusStyles[job.status].variant}>
            {statusStyles[job.status].label}
          </Badge>
        </div>
      ))}
    </div>
  );
}
