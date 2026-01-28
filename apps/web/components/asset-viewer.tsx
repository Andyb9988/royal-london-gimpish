import type { Asset, AssetKind } from "@/lib/api/types";
import { buildPublicAssetUrl } from "@/lib/api/asset-url";

function pickAsset(assets: Asset[], kind: AssetKind) {
  return assets.find((asset) => asset.kind === kind && asset.status === "ready");
}

export function AssetViewer({ assets }: { assets: Asset[] }) {
  const imageAsset = pickAsset(assets, "gimpified_image");
  const videoAsset = pickAsset(assets, "video");

  const imageUrl = imageAsset ? buildPublicAssetUrl(imageAsset) : null;
  const videoUrl = videoAsset ? buildPublicAssetUrl(videoAsset) : null;

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <p className="text-sm font-medium text-ink">Gimpified image</p>
        {imageUrl ? (
          <img
            src={imageUrl}
            alt="Gimpified highlight"
            className="mt-3 w-full rounded-xl object-cover"
          />
        ) : (
          <p className="mt-4 text-sm text-muted">
            Gimpified image not ready yet or bucket not configured.
          </p>
        )}
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <p className="text-sm font-medium text-ink">Video highlight</p>
        {videoUrl ? (
          <video
            controls
            preload="metadata"
            className="mt-3 w-full rounded-xl"
          >
            <source src={videoUrl} />
          </video>
        ) : (
          <p className="mt-4 text-sm text-muted">
            Video not ready yet or bucket not configured.
          </p>
        )}
      </div>
    </div>
  );
}
