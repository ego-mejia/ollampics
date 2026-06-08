import { Link } from "react-router-dom";
import tw from "tailwind-styled-components";

export const PageWrap = tw.div`max-w-6xl mx-auto px-8 py-10`;
export const BackLink = tw(Link)`
  text-brand-blue text-sm hover:underline no-underline
`;
export const TitleRow = tw.div`mt-2 mb-1 flex items-center gap-3`;
export const PageTitle = tw.h1`text-2xl font-medium text-fg`;
export const MetaRow = tw.p`text-sm text-fg-dim mb-6`;

export const DeleteBtn = tw.button`
  ml-auto inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded
  text-xs text-fg-dim border border-border-soft
  hover:text-brand-red hover:border-brand-red/50 hover:bg-brand-red/5
  transition-colors disabled:opacity-50 disabled:cursor-not-allowed
`;

