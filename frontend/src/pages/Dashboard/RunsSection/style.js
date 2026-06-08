import { Link } from "react-router-dom";
import tw from "tailwind-styled-components";

export const Section = tw.section``;

export const IdLink = tw(Link)`
  text-brand-blue hover:underline font-medium no-underline
`;

export const SuccessCount = tw.span`text-brand-green font-medium tabular-nums`;
export const TotalCount = tw.span`text-fg-dim tabular-nums`;

export const EmptyCode = tw.code`
  bg-elev/60 px-1.5 py-0.5 rounded text-fg-muted
`;

export const DeleteBtn = tw.button`
  p-1.5 rounded text-fg-dim hover:text-brand-red hover:bg-brand-red/10
  transition-colors opacity-0 group-hover:opacity-100
`;

