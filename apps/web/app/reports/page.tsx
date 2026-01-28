import Link from "next/link";

import { ReportList } from "@/components/report-list";
import { SectionHeader } from "@/components/section-header";
import { buttonVariants } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { cn } from "@/lib/utils";
import { listReports } from "@/lib/api/reports";

const PAGE_SIZE = 12;

export default async function ReportsPage({
  searchParams,
}: {
  searchParams: { page?: string; opponent?: string };
}) {
  const page = Number(searchParams.page ?? "1");
  const safePage = Number.isNaN(page) || page < 1 ? 1 : page;
  const offset = (safePage - 1) * PAGE_SIZE;

  const reports = await listReports(
    {
      status: "published",
      opponent: searchParams.opponent,
      limit: PAGE_SIZE,
      offset,
    },
    { next: { revalidate: 60 } },
  ).catch((error) => {
    if (error instanceof ApiError || error instanceof TypeError) {
      return [];
    }
    throw error;
  });

  const showNext = reports.length === PAGE_SIZE;
  const prevPage = Math.max(safePage - 1, 1);
  const nextPage = safePage + 1;

  return (
    <div className="space-y-10">
      <SectionHeader
        title="Report archive"
        subtitle="Explore published match reports."
      />

      <ReportList reports={reports} hrefPrefix="/reports" />

      <div className="flex items-center justify-between">
        <Link
          href={`/reports?page=${prevPage}`}
          className={buttonVariants({ variant: "outline" })}
        >
          Previous
        </Link>
        <span className="text-sm text-muted">Page {safePage}</span>
        <Link
          href={`/reports?page=${nextPage}`}
          className={cn(
            buttonVariants({ variant: "outline" }),
            !showNext && "pointer-events-none opacity-50",
          )}
          aria-disabled={!showNext}
        >
          Next
        </Link>
      </div>
    </div>
  );
}
