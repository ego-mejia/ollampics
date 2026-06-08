import tw from "tailwind-styled-components";

export const Wrap = tw.div``;

export const Hint = tw.p`
  text-xs text-fg-dim mb-3 leading-relaxed
`;

export const PromptRow = tw.div`
  border-t border-border-soft py-3 px-4
`;

export const PromptHeader = tw.div`flex items-baseline justify-between gap-3`;

export const PromptName = tw.code`
  font-mono text-sm text-fg
`;

export const PromptMeta = tw.span`
  text-xs text-fg-dim tabular-nums whitespace-nowrap
`;

export const ToggleBtn = tw.button`
  text-xs text-brand-blue mt-2 hover:underline
`;

export const Content = tw.pre`
  bg-elev/40 border border-border-soft rounded p-3 mt-2
  text-xs text-fg whitespace-pre-wrap font-mono leading-relaxed
  max-h-96 overflow-y-auto
`;
