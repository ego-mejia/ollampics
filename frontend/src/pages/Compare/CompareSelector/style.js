import tw from "tailwind-styled-components";

export const Row = tw.div`grid grid-cols-2 gap-4 mb-6`;

export const Field = tw.div``;

export const Label = tw.label`
  block text-xs uppercase tracking-wider text-fg-dim mb-1 font-medium
`;

export const Select = tw.select`
  w-full bg-card border border-border rounded px-3 py-2 text-sm text-fg
  focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30
`;

export const Hint = tw.p`
  text-xs text-fg-dim mt-1
`;
