import { Link } from "react-router-dom";
import tw from "tailwind-styled-components";

export const PageWrap = tw.div`max-w-5xl mx-auto px-8 py-12`;

export const Section = tw.section`mb-16`;

export const SectionTitle = tw.h2`
  text-xl font-medium text-fg mb-4
`;

export const Prose = tw.p`
  text-base text-fg-muted leading-relaxed mb-3
`;

export const InlineCode = tw.code`
  bg-elev/60 px-1.5 py-0.5 rounded text-sm font-mono text-fg
`;

export const CodeBlock = tw.div`
  bg-card border border-border rounded-lg p-4 font-mono text-sm text-fg
  overflow-x-auto whitespace-pre my-3
`;

export const CTALink = tw.a`
  inline-flex items-center text-brand-blue hover:underline font-medium
`;

export const CTARouterLink = tw(Link)`
  inline-flex items-center
  bg-brand-blue text-white px-5 py-2.5 rounded text-sm font-medium
  hover:bg-brand-blue/90 shadow-sm transition-colors no-underline
`;

export const CTASecondary = tw(Link)`
  inline-flex items-center
  border border-border text-fg px-5 py-2.5 rounded text-sm font-medium
  hover:bg-elev/50 transition-colors no-underline
`;

export const CTAGroup = tw.div`flex flex-wrap gap-3 mt-6`;
