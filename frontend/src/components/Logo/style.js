import tw from "tailwind-styled-components";

// CSS mask trick: the bg-fg color fills the SVG silhouette, so the logo
// adopts whatever text color its parent has. In dark theme, --fg is white;
// in light, it's near-black.
export const LogoMark = tw.span`
  inline-block
  bg-fg
  [mask-image:url('/logo.svg')]
  [mask-repeat:no-repeat]
  [mask-position:center]
  [mask-size:contain]
  [-webkit-mask-image:url('/logo.svg')]
  [-webkit-mask-repeat:no-repeat]
  [-webkit-mask-position:center]
  [-webkit-mask-size:contain]
`;
