import tw from "tailwind-styled-components";

export const Rank = tw.td`px-4 py-2.5 font-semibold tabular-nums text-base`;
export const RankYellow = tw.td`px-4 py-2.5 font-semibold tabular-nums text-lg leading-none text-brand-yellow`;
export const RankSky = tw.td`px-4 py-2.5 font-semibold tabular-nums text-lg leading-none text-brand-sky`;
export const RankOrange = tw.td`px-4 py-2.5 font-semibold tabular-nums text-lg leading-none text-brand-orange`;
export const RankDim = tw.td`px-4 py-2.5 font-semibold tabular-nums text-fg-dim`;

export const BarTrack = tw.div`
  flex-1 bg-elev/60 rounded-full h-1.5 overflow-hidden
`;
export const BarFill = tw.div`bg-brand-green h-full transition-[width] duration-300`;

export const BarRow = tw.div`flex items-center gap-2`;
export const BarText = tw.span`text-xs text-fg w-24 text-right tabular-nums`;
