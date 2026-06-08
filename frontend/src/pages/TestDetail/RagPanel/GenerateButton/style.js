import tw from "tailwind-styled-components";

export const ButtonsRow = tw.div`
  flex items-center gap-3 mb-6
`;

export const Status = tw.span`
  text-sm text-brand-magenta animate-pulse
`;

export const Idle = tw.span`
  text-xs text-fg-dim
`;
