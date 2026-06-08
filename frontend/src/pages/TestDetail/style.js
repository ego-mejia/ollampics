import { Link } from "react-router-dom";
import tw from "tailwind-styled-components";

export const PageWrap = tw.div`max-w-5xl mx-auto px-8 py-10`;

export const BackLink = tw(Link)`
  text-brand-blue text-sm hover:underline no-underline
`;

export const TitleRow = tw.div`mt-2 mb-1 flex items-center gap-3`;

export const Icon = tw.span`text-2xl leading-none`;

export const PageTitle = tw.h1`text-2xl font-medium text-fg`;

export const Desc = tw.p`text-sm text-fg-dim mb-8 leading-relaxed`;
