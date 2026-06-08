import { Link } from "react-router-dom";
import tw from "tailwind-styled-components";

export const CardLink = tw(Link)`
  block bg-card border border-border rounded-lg p-5
  no-underline transition-all
  hover:border-brand-blue/40 hover:shadow-sm
`;

export const CardHeader = tw.div`flex items-start justify-between mb-3`;

export const IconBlock = tw.div`
  text-2xl leading-none
`;

export const TasksBadge = tw.span`
  text-xs px-2 py-0.5 rounded font-medium
  bg-elev/60 text-fg-muted tabular-nums
`;

export const CorpusBadge = tw.span`
  text-xs px-2 py-0.5 rounded font-medium
  bg-brand-green/15 text-brand-green ml-1
`;

export const Title = tw.h3`
  text-base font-medium text-fg mb-1
`;

export const Desc = tw.p`
  text-sm text-fg-muted leading-relaxed mb-4
`;

export const OpenAction = tw.div`
  text-xs text-brand-blue font-medium uppercase tracking-wider
`;
