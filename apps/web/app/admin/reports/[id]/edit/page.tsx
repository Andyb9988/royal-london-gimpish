"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";

import { AssetViewer } from "@/components/asset-viewer";
import { EmptyState } from "@/components/empty-state";
import { GimpImageUpload } from "@/components/gimp-image-upload";
import { JobProgress } from "@/components/job-progress";
import { ReportForm, type ReportFormValues } from "@/components/report-form";
import { SectionHeader } from "@/components/section-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  publishReport,
  submitReport,
  unpublishReport,
  updateReport,
} from "@/lib/api/reports";
import type { ReportDetail } from "@/lib/api/types";
import { POLL_INTERVAL_MS } from "@/lib/config";

export default function ReportEditPage({
  params,
}: {
  params: { id: string };
}) {
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, error, mutate } = useSWR<ReportDetail>(
    `/v1/reports/${params.id}`,
    {
      refreshInterval: (latest) =>
        latest?.status === "processing" ? POLL_INTERVAL_MS : 0,
    },
  );

  const canPublish = useMemo(() => {
    if (!data) return false;
    const requiredAssets = ["gimpified_image", "video"];
    const assetsReady = requiredAssets.every((kind) =>
      data.assets.some((asset) => asset.kind === kind && asset.status === "ready"),
    );
    const jobsReady = data.jobs.every((job) => job.status === "succeeded");
    return data.status !== "published" && assetsReady && jobsReady;
  }, [data]);

  const handleSave = async (values: ReportFormValues) => {
    if (!data) return;
    setSaving(true);
    setActionError(null);
    try {
      await updateReport(data.id, {
        date: values.date,
        opponent: values.opponent,
        content: values.content,
      });
      await mutate();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (!data) return;
    setActionError(null);
    try {
      await submitReport(data.id);
      await mutate();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Submit failed");
    }
  };

  const handlePublish = async () => {
    if (!data) return;
    setActionError(null);
    try {
      await publishReport(data.id);
      await mutate();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Publish failed");
    }
  };

  const handleUnpublish = async () => {
    if (!data) return;
    setActionError(null);
    try {
      await unpublishReport(data.id);
      await mutate();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Unpublish failed");
    }
  };

  if (error) {
    return (
      <EmptyState
        title="Report unavailable"
        description="Check the report ID and API connection."
      />
    );
  }

  if (!data) {
    return (
      <div className="card-surface p-8">
        <p className="text-sm text-muted">Loading report...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <SectionHeader
        title="Edit report"
        subtitle={`Report ${data.id}`}
        action={<StatusBadge status={data.status} />}
      />

      {actionError ? (
        <Card className="border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {actionError}
        </Card>
      ) : null}

      <ReportForm report={data} onSave={handleSave} saving={saving} />

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <GimpImageUpload reportId={data.id} onUploaded={() => mutate()} />

        <Card className="p-6">
          <h3 className="text-base font-semibold text-ink">Derived fields</h3>
          <div className="mt-4 space-y-4 text-sm">
            <div>
              <p className="text-muted">Gimp name</p>
              <p className="font-medium text-ink">
                {data.gimp_name ?? "Pending"}
              </p>
            </div>
            <div>
              <p className="text-muted">Champagne moment</p>
              <p className="font-medium text-ink">
                {data.champagne_moment ?? "Pending"}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Card className="p-6">
          <h3 className="text-base font-semibold text-ink">Job progress</h3>
          <div className="mt-4">
            <JobProgress jobs={data.jobs} />
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-base font-semibold text-ink">Actions</h3>
          <div className="mt-4 flex flex-col gap-3">
            {(data.status === "draft" || data.status === "failed") && (
              <Button type="button" onClick={handleSubmit}>
                Submit for processing
              </Button>
            )}
            {data.status === "processing" && (
              <Button type="button" variant="secondary" disabled>
                Processing...
              </Button>
            )}
            {canPublish && (
              <Button type="button" variant="default" onClick={handlePublish}>
                Publish report
              </Button>
            )}
            {data.status === "published" && (
              <Button type="button" variant="outline" onClick={handleUnpublish}>
                Unpublish
              </Button>
            )}
          </div>
        </Card>
      </section>

      <section className="space-y-4">
        <h3 className="text-base font-semibold text-ink">Media preview</h3>
        <AssetViewer assets={data.assets} />
      </section>
    </div>
  );
}
