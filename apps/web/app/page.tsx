import Link from "next/link";

import { SectionHeader } from "@/components/section-header";
import { ReportList } from "@/components/report-list";
import { buttonVariants } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { listReports } from "@/lib/api/reports";

export default async function Home() {
  const reports = await listReports(
    { status: "published", limit: 6, offset: 0 },
    { next: { revalidate: 60 } },
  ).catch((error) => {
    if (error instanceof ApiError || error instanceof TypeError) {
      return [];
    }
    throw error;
  });

  return (
    <div className="space-y-12">
      <SectionHeader
        title="Gimpish match reports"
        subtitle="Latest stories, gimpified highlights, and a champagne moment for every match."
        action={
          <Link
            href="/reports"
            className={buttonVariants({ size: "lg" })}
          >
            Browse archive
          </Link>
        }
      />

      <section className="grid gap-6 rounded-3xl border border-slate-200 bg-white p-8">
        <div>
          <p className="text-sm font-medium text-ink">This week</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink">
            The gimp of the week awaits
          </h2>
          <p className="mt-2 text-muted">
            Create a report, upload the gimp, and let the pipeline do the rest.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/admin"
            className={buttonVariants({ variant: "secondary" })}
          >
            Open dashboard
          </Link>
          <Link
            href="/admin/reports/new"
            className={buttonVariants({ variant: "outline" })}
          >
            Start new report
          </Link>
        </div>
      </section>

      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-ink">Latest reports</h2>
          <Link href="/reports" className="text-sm text-accent">
            See all
          </Link>
        </div>
        <ReportList reports={reports} hrefPrefix="/reports" />
      </section>
    </div>
  );
}
