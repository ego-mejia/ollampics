import { CardWrap, StatCard, StatLabel, StatValue, StatValueSuccess } from "./style";

type Props = { children: React.ReactNode; className?: string };

export default function Card({ children, className }: Props) {
  return <CardWrap className={className}>{children}</CardWrap>;
}

type StatProps = { title: string; value: string; variant?: "default" | "success" };

export function Stat({ title, value, variant = "default" }: StatProps) {
  const Value = variant === "success" ? StatValueSuccess : StatValue;
  return (
    <StatCard>
      <StatLabel>{title}</StatLabel>
      <Value>{value}</Value>
    </StatCard>
  );
}
