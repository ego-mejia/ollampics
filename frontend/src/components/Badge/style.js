import tw from "tailwind-styled-components";

export const BadgeSuccess = tw.span`
  inline-flex items-center
  text-xs px-2 py-0.5 rounded font-medium
  bg-brand-green/15 text-brand-green
`;

export const BadgeFail = tw.span`
  inline-flex items-center
  text-xs px-2 py-0.5 rounded font-medium
  bg-brand-red/15 text-brand-red
`;

export const BadgeWarn = tw.span`
  inline-flex items-center
  text-xs px-2 py-0.5 rounded font-medium
  bg-brand-yellow/20 text-brand-yellow
`;

export const BadgeNeutral = tw.span`
  inline-flex items-center
  text-xs px-2 py-0.5 rounded font-medium
  bg-elev text-fg-muted
`;

export const BadgeLive = tw.span`
  inline-flex items-center
  text-xs px-2 py-0.5 rounded font-medium
  bg-brand-magenta/15 text-brand-magenta animate-pulse
`;
