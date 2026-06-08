import tw from "tailwind-styled-components";

export const Wrap = tw.div`
  flex items-start gap-5 mb-6 p-5
  bg-card border border-border rounded-lg
`;

export const IconSlot = tw.div`
  flex-shrink-0 flex items-center justify-center text-fg
`;

export const Body = tw.div`flex-1 min-w-0`;

export const Title = tw.h2`
  text-lg font-medium text-fg mb-1
`;

export const Desc = tw.p`
  text-sm text-fg-muted leading-relaxed
`;
