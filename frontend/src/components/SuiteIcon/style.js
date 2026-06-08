import tw from "tailwind-styled-components";

// Generic theme-aware icon based on CSS mask. The URL is set via inline style
// at the call site so we can reuse this component for any /icons/*.svg.
export const Mask = tw.span`
  inline-block bg-fg align-middle
`;
