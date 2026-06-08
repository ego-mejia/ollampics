import { Link } from "react-router-dom";
import tw from "tailwind-styled-components";

export const Primary = tw.button`
  bg-brand-blue text-white px-4 py-2 rounded text-sm font-medium
  hover:bg-brand-blue/90 disabled:opacity-30 disabled:cursor-not-allowed
  shadow-sm transition-colors inline-flex items-center justify-center
`;

export const PrimaryRouterLink = tw(Link)`
  bg-brand-blue text-white px-4 py-2 rounded text-sm font-medium
  hover:bg-brand-blue/90 shadow-sm transition-colors no-underline
  inline-flex items-center justify-center
`;

export const IconBtn = tw.button`
  p-2 rounded text-fg-muted
  hover:text-fg hover:bg-elev/70 transition-colors
`;
