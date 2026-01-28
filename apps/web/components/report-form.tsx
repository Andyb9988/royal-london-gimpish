"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Report } from "@/lib/api/types";

export interface ReportFormValues {
  date: string;
  opponent: string;
  content: string;
}

export function ReportForm({
  report,
  onSave,
  saving,
}: {
  report: Report;
  onSave: (values: ReportFormValues) => Promise<void>;
  saving: boolean;
}) {
  const [values, setValues] = useState<ReportFormValues>({
    date: report.date,
    opponent: report.opponent ?? "",
    content: report.content ?? "",
  });

  useEffect(() => {
    setValues({
      date: report.date,
      opponent: report.opponent ?? "",
      content: report.content ?? "",
    });
  }, [report]);

  return (
    <Card className="p-6">
      <div className="grid gap-6">
        <div className="grid gap-2">
          <Label htmlFor="date">Match date</Label>
          <Input
            id="date"
            type="date"
            value={values.date}
            onChange={(event) =>
              setValues((prev) => ({ ...prev, date: event.target.value }))
            }
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="opponent">Opponent</Label>
          <Input
            id="opponent"
            placeholder="Club name"
            value={values.opponent}
            onChange={(event) =>
              setValues((prev) => ({ ...prev, opponent: event.target.value }))
            }
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="content">Match report</Label>
          <Textarea
            id="content"
            placeholder="Write the match report..."
            value={values.content}
            onChange={(event) =>
              setValues((prev) => ({ ...prev, content: event.target.value }))
            }
          />
        </div>
        <div className="flex justify-end">
          <Button
            type="button"
            onClick={() => onSave(values)}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save changes"}
          </Button>
        </div>
      </div>
    </Card>
  );
}
