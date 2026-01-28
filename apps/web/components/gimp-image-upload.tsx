"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { createAssetUploadUrl, attachAsset } from "@/lib/api/assets";
import { uploadToSignedUrl } from "@/lib/api/client";

export function GimpImageUpload({
  reportId,
  onUploaded,
}: {
  reportId: string;
  onUploaded: () => void;
}) {
  const [status, setStatus] = useState<
    "idle" | "requesting" | "uploading" | "attaching" | "error" | "done"
  >("idle");
  const [message, setMessage] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setStatus("requesting");
    setMessage(null);

    try {
      const upload = await createAssetUploadUrl(reportId, {
        kind: "gimp_original",
        mime_type: file.type,
      });

      if (!upload.upload_url) {
        throw new Error(
          "Upload URL not available. Configure signed uploads in the API.",
        );
      }

      setStatus("uploading");
      await uploadToSignedUrl(upload.upload_url, file);

      setStatus("attaching");
      await attachAsset(reportId, {
        kind: "gimp_original",
        gcs_path: upload.gcs_path,
        mime_type: file.type,
        size_bytes: file.size,
      });

      setStatus("done");
      onUploaded();
    } catch (error) {
      setStatus("error");
      setMessage(
        error instanceof Error ? error.message : "Upload failed unexpectedly",
      );
    }
  };

  return (
    <Card className="p-6">
      <div className="flex flex-col gap-4">
        <div>
          <p className="text-sm font-medium text-ink">Gimp of the day</p>
          <p className="text-sm text-muted">
            Upload the source image for gimpification.
          </p>
        </div>
        <input
          type="file"
          accept="image/*"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              void handleFile(file);
            }
          }}
        />
        {status === "uploading" && (
          <p className="text-sm text-muted">Uploading image...</p>
        )}
        {status === "attaching" && (
          <p className="text-sm text-muted">Linking asset...</p>
        )}
        {status === "done" && (
          <p className="text-sm text-emerald-600">Upload complete.</p>
        )}
        {status === "error" && (
          <p className="text-sm text-rose-600">{message}</p>
        )}
        <Button
          type="button"
          variant="outline"
          onClick={() => onUploaded()}
        >
          Refresh assets
        </Button>
      </div>
    </Card>
  );
}
