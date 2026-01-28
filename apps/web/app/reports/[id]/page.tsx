import { notFound } from "next/navigation";

import { AssetViewer } from "@/components/asset-viewer";
import { SectionHeader } from "@/components/section-header";
import { getReport } from "@/lib/api/reports";

export default async function ReportDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const report = await getReport(params.id, { next: { revalidate: 30 } });

  if (report.status !== "published") {
    notFound();
  }

  return (
    <div className="space-y-10">
      <SectionHeader
        title={report.opponent ?? "Match report"}
        subtitle={new Date(report.date).toLocaleDateString()}
      />

      <section className="card-surface p-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-sm font-medium text-muted">Gimp name</p>
            <p className="mt-1 text-lg font-semibold text-ink">
              {report.gimp_name ?? "Pending"}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-muted">Champagne moment</p>
            <p className="mt-1 text-lg font-semibold text-ink">
              {report.champagne_moment ?? "Pending"}
            </p>
          </div>
        </div>
      </section>

      <section className="card-surface p-6">
        <h2 className="text-lg font-semibold text-ink">Match report</h2>
        <p className="mt-3 whitespace-pre-line text-sm text-slate-700">
          {report.content ?? "No report available."}
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-ink">Media</h2>
        <AssetViewer assets={report.assets} />
      </section>
    </div>
  );
}
