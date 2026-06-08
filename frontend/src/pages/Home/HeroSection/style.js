import tw from "tailwind-styled-components";

export const Wrap = tw.section`
  flex flex-col items-center text-center py-8 mb-12
`;

export const LogoSlot = tw.div`
  mb-6 text-fg
`;

export const Tagline = tw.h1`
  text-3xl md:text-4xl font-medium text-fg mb-3 max-w-2xl
`;

export const Subtitle = tw.p`
  text-base md:text-lg text-fg-muted leading-relaxed max-w-3xl
`;
