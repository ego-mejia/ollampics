import { LogoMark } from "./style";

type Props = { size?: number; ariaLabel?: string };

export default function Logo({ size = 26, ariaLabel = "OLLAMPICS" }: Props) {
  return (
    <LogoMark
      role="img"
      aria-label={ariaLabel}
      style={{ width: size, height: size }}
    />
  );
}
