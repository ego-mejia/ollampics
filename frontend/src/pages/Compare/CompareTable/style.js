import tw from "tailwind-styled-components";

export const Section = tw.section`mb-8`;

export const Summary = tw.div`
  grid grid-cols-4 gap-3 mb-4
`;

export const StatBox = tw.div`
  bg-card border border-border rounded-lg p-3
`;

export const StatLabel = tw.div`
  text-xs uppercase tracking-wider text-fg-dim
`;

export const StatValue = tw.div`
  text-xl font-medium mt-1 text-fg tabular-nums
`;

export const StatValueAccent = tw.div`
  text-xl font-medium mt-1 text-brand-green tabular-nums
`;

export const StatValueWarn = tw.div`
  text-xl font-medium mt-1 text-brand-yellow tabular-nums
`;

export const StatusSuccess = tw.td`px-3 py-2 font-medium text-brand-green text-center`;
export const StatusFail = tw.td`px-3 py-2 font-medium text-brand-yellow text-center`;
export const StatusError = tw.td`px-3 py-2 font-medium text-brand-red text-center`;
export const StatusMissing = tw.td`px-3 py-2 text-fg-dim text-center`;

export const DiffPlus = tw.span`text-brand-green text-xs ml-1`;
export const DiffMinus = tw.span`text-brand-red text-xs ml-1`;
