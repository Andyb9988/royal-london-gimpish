"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";

import { EmptyState } from "@/components/empty-state";
import { ReportList } from "@/components/report-list";
import { SectionHeader } from "@/components/section-header";
import { StatusFilter } from "@/components/admin/status-filter";
import { buttonVariants } from "@/components/ui/button";
import type { Report, ReportStatus } from "@/lib/api/types";

const REPORTS_KEY = "/v1/reports?limit=100&offset=0";

export default function AdminDashboard() {
  const { data, error } = useSWR<Report[]>(REPORTS_KEY);
  const [filter, setFilter] = useState<ReportStatus | "all">("all");

  if (error) {
    return (
      <EmptyState
        title="Failed to load reports"
        description="Check that the API is running and the author header is set."
      />
    );
  }

  if (!data) {
    return (
      <div className="card-surface p-8">
        <p className="text-sm text-muted">Loading dashboard...</p>
      </div>
    );
  }

  const reports =
    filter === "all" ? data : data.filter((report) => report.status === filter);

  return (
    <div className="space-y-8">
      <SectionHeader
        title="Admin dashboard"
        subtitle="Track drafts, monitor processing, and publish reports."
        action={
          <Link
            href="/admin/reports/new"
            className={buttonVariants({ variant: "default" })}
          >
            New report
          </Link>
        }
      />

      <StatusFilter value={filter} onChange={setFilter} />

      {reports.length ? (
        <ReportList reports={reports} hrefPrefix="/admin/reports" />
      ) : (
        <EmptyState
          title="No reports in this view"
          description="Create a report to see it here."
        />
      )}
    </div>
  );
}
