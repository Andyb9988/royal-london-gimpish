import { Badge } from "@/components/ui/badge";
import type { ReportStatus } from "@/lib/api/types";

const statusMap: Record<
  ReportStatus,
  { label: string; variant: "default" | "success" | "warning" | "error" }
> = {
  draft: { label: "Draft", variant: "default" },
  processing: { label: "Processing", variant: "warning" },
  failed: { label: "Failed", variant: "error" },
  published: { label: "Published", variant: "success" },
  archived: { label: "Archived", variant: "default" },
};

export function StatusBadge({ status }: { status: ReportStatus }) {
  const { label, variant } = statusMap[status];
  return <Badge variant={variant}>{label}</Badge>;
}
