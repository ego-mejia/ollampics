import tw from "tailwind-styled-components";

export const SelectorBox = tw.div`
  bg-card border border-border rounded-lg p-2 space-y-0.5
`;

export const RowLabel = tw.label`
  flex items-center gap-3 px-2 py-1.5 rounded
  hover:bg-elev/60 cursor-pointer transition-colors
`;

export const Checkbox = tw.input`accent-brand-blue`;

export const SuiteName = tw.span`font-mono text-sm text-fg flex-1`;

export const TasksText = tw.span`text-xs text-fg-dim tabular-nums`;

export const CountAccent = tw.span`text-brand-blue tabular-nums`;
