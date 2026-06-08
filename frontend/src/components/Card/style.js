import tw from "tailwind-styled-components";

export const CardWrap = tw.div`
  bg-card border border-border rounded-lg overflow-hidden
`;

export const StatCard = tw.div`
  bg-card border border-border rounded-lg p-4
`;

export const StatLabel = tw.div`
  text-xs uppercase tracking-wider text-fg-dim
`;

export const StatValue = tw.div`
  text-2xl font-medium mt-1 text-fg
`;

export const StatValueSuccess = tw.div`
  text-2xl font-medium mt-1 text-brand-green
`;
