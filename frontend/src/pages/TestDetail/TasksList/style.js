import tw from "tailwind-styled-components";

export const Section = tw.section`mb-10`;

export const Row = tw.div`
  border-t border-border-soft py-3
  grid grid-cols-[1fr_auto] gap-4
`;

export const TaskId = tw.code`
  font-mono text-xs text-brand-blue
`;

export const TaskDesc = tw.div`
  text-sm text-fg mt-1
`;

export const Triesmall = tw.span`
  text-xs text-fg-dim tabular-nums whitespace-nowrap
`;
