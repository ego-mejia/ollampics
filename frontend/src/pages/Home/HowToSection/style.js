import tw from "tailwind-styled-components";

export const Steps = tw.div`
  grid grid-cols-1 md:grid-cols-3 gap-4 mt-4
`;

export const Step = tw.div`
  bg-card border border-border rounded-lg p-5 flex flex-col
`;

export const StepIconWrap = tw.div`
  h-20 flex items-center justify-center mb-3 text-fg-muted
`;

export const StepTitle = tw.h3`
  text-base font-medium text-fg mb-2
`;

export const StepBody = tw.p`
  text-sm text-fg-muted leading-relaxed
`;

export const StepCode = tw.code`
  block bg-elev/60 px-3 py-2 rounded mt-3 text-xs font-mono text-fg overflow-x-auto
`;

export const StepLink = tw.a`
  inline-block text-brand-blue text-sm hover:underline mt-2
`;

export const SuiteGrid = tw.div`
  grid grid-cols-3 gap-3 mt-4 mb-2 text-fg-muted
`;

export const SuiteTile = tw.div`
  flex flex-col items-center gap-1.5 p-2 rounded-md
  bg-elev/30 border border-border-soft
`;

export const SuiteLabel = tw.span`
  text-[10px] uppercase tracking-wider text-fg-dim
`;
