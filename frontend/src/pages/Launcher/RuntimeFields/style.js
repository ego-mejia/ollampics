import tw from "tailwind-styled-components";

export const Row = tw.section`grid grid-cols-2 gap-4`;
export const Field = tw.div``;
export const FieldLabel = tw.label`
  block text-xs uppercase tracking-wider text-fg-dim mb-2 font-medium
`;
export const NumberInput = tw.input`
  w-full bg-card border border-border rounded px-3 py-2 text-fg
  focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30
  transition-shadow
`;
export const Select = tw.select`
  w-full bg-card border border-border rounded px-3 py-2 text-fg
  focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30
  transition-shadow
`;
export const TextInput = tw.input`
  w-full bg-card border border-border rounded px-3 py-2 text-fg
  placeholder:text-fg-dim
  focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30
  transition-shadow
`;
