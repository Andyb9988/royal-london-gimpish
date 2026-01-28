import { redirect } from "next/navigation";

export default function ReportEditRedirect({
  params,
}: {
  params: { id: string };
}) {
  redirect(`/admin/reports/${params.id}/edit`);
}
