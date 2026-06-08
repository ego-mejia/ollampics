import tw from "tailwind-styled-components";

export const FiltersRow = tw.div`
  flex flex-wrap gap-3 mb-6
`;

export const Field = tw.div`min-w-[160px]`;

export const FieldLabel = tw.label`
  block text-xs uppercase tracking-wider text-fg-dim mb-1 font-medium
`;

export const Select = tw.select`
  bg-card border border-border rounded px-3 py-1.5 text-sm text-fg w-full
  focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30
  transition-shadow
`;
