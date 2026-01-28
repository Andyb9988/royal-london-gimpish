"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { createReport } from "@/lib/api/reports";

export default function NewReportPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const create = async () => {
      try {
        const today = new Date().toISOString().slice(0, 10);
        const report = await createReport({ date: today });
        router.replace(`/admin/reports/${report.id}/edit`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create report");
      }
    };

    void create();
  }, [router]);

  return (
    <div className="card-surface p-8">
      <p className="text-sm text-muted">Creating draft report...</p>
      {error ? <p className="mt-2 text-sm text-rose-600">{error}</p> : null}
    </div>
  );
}
