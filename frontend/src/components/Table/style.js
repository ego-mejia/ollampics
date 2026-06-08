import tw from "tailwind-styled-components";

// Editorial table — soft surfaces, subtle dividers (Linear / Vercel pattern).

export const Table = tw.table`w-full`;

export const THead = tw.thead`
  bg-elev/60 border-b border-border-soft
  text-xs uppercase tracking-wider text-fg-dim
`;

export const TBody = tw.tbody``;

export const HeaderRow = tw.tr``;

export const Row = tw.tr`
  border-t border-border-soft hover:bg-elev/40 transition-colors
`;

// — Headers —
export const TH = tw.th`text-left px-4 py-2.5 font-medium`;
export const THRight = tw.th`text-right px-4 py-2.5 font-medium`;
export const THCompact = tw.th`text-left px-4 py-2.5 font-medium w-12`;

// — Cells —
export const TD = tw.td`px-4 py-2.5 text-fg`;
export const TDRight = tw.td`px-4 py-2.5 text-right text-fg`;
export const TDMuted = tw.td`px-4 py-2.5 text-fg-muted`;
export const TDMutedRight = tw.td`px-4 py-2.5 text-right text-fg-muted`;
export const TDMono = tw.td`px-4 py-2.5 font-mono text-xs text-fg`;
export const TDMonoMuted = tw.td`px-4 py-2.5 font-mono text-xs text-fg-muted`;
export const TDEmpty = tw.td`px-4 py-6 text-center text-fg-dim`;
