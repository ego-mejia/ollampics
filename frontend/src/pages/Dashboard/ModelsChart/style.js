import tw from "tailwind-styled-components";

export const Wrap = tw.section`
  bg-card border border-border rounded-lg p-5 mb-10
`;

export const Header = tw.div`flex items-baseline justify-between mb-3`;

export const Title = tw.h2`
  text-sm uppercase tracking-wider text-fg-dim font-medium
`;

export const Sub = tw.span`text-xs text-fg-dim`;

export const Empty = tw.div`
  text-fg-dim text-sm py-8 text-center
`;
