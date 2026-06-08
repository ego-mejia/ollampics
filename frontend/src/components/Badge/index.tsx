import {
  BadgeFail,
  BadgeLive,
  BadgeNeutral,
  BadgeSuccess,
  BadgeWarn,
} from "./style";

type Variant = "success" | "fail" | "warn" | "neutral" | "live";

type Props = { variant: Variant; children: React.ReactNode };

const components = {
  success: BadgeSuccess,
  fail: BadgeFail,
  warn: BadgeWarn,
  neutral: BadgeNeutral,
  live: BadgeLive,
};

export default function Badge({ variant, children }: Props) {
  const C = components[variant];
  return <C>{children}</C>;
}

/** Convenience: map a run/attempt status string to a Badge variant. */
export function StatusBadge({ status }: { status: string }) {
  const v: Variant =
    status === "success" || status === "done"
      ? "success"
      : status === "running" || status === "queued"
      ? "live"
      : status === "fail"
      ? "warn"
      : status === "error" || status === "failed" || status === "timeout"
      ? "fail"
      : "neutral";
  return <Badge variant={v}>{status}</Badge>;
}
