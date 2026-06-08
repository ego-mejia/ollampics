import { Mask } from "./style";

const SUITE_TO_FILE: Record<string, string> = {
  baseline: "baseline.svg",
  tool_calling: "tool_calling.svg",
  rag: "rag.svg",
  planning: "planning.svg",
  personal_agent: "personal_agent.svg",
  multi_agent: "multi_agent.svg",
  all: "all.svg",
  compare: "compare.svg",
};

type Props = {
  name: string;
  size?: number;
  ariaLabel?: string;
};

/** Theme-aware icon for a suite (or "all", "compare"). Uses CSS mask so the
 *  silhouette adopts the current text color (white in dark mode, dark in light).
 */
export default function SuiteIcon({ name, size = 64, ariaLabel }: Props) {
  const file = SUITE_TO_FILE[name] || SUITE_TO_FILE.all;
  const url = `/icons/${file}`;
  return (
    <Mask
      role="img"
      aria-label={ariaLabel || name}
      style={{
        width: size,
        height: size,
        WebkitMaskImage: `url(${url})`,
        maskImage: `url(${url})`,
        WebkitMaskRepeat: "no-repeat",
        maskRepeat: "no-repeat",
        WebkitMaskPosition: "center",
        maskPosition: "center",
        WebkitMaskSize: "contain",
        maskSize: "contain",
      }}
    />
  );
}
