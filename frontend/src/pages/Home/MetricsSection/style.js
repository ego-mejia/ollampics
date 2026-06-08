import tw from "tailwind-styled-components";

export const Grid = tw.div`
  grid grid-cols-1 md:grid-cols-2 gap-3 mt-2
`;

export const Row = tw.div`
  bg-card border border-border rounded-lg p-4
`;

export const MetricName = tw.div`
  font-mono text-sm text-brand-blue mb-1
`;

export const MetricDesc = tw.p`
  text-sm text-fg-muted leading-relaxed
`;
