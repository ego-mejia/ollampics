import { Link } from "react-router-dom";
import tw from "tailwind-styled-components";

export const LayoutRoot = tw.div`min-h-screen bg-bg text-fg`;

export const TopBar = tw.header`
  border-b border-border-soft bg-card/70 backdrop-blur
  sticky top-0 z-10
`;

export const TopBarInner = tw.div`
  max-w-6xl mx-auto px-8 h-14
  flex items-center justify-between
`;

export const BrandLink = tw(Link)`
  flex items-center gap-2.5 text-fg no-underline
`;

export const BrandText = tw.span`
  text-base font-semibold tracking-tight text-fg
`;

export const RightCluster = tw.div`flex items-center gap-2`;

export const NavWrap = tw.nav`flex gap-1`;

// NavLink expects className as string or function — these are exported as raw strings
// so Layout can pass them directly to <NavLink className={...}>.
export const NAV_ACTIVE_CLASS =
  "text-sm px-3 py-1.5 rounded bg-brand-blue/15 text-brand-blue font-medium no-underline";

export const NAV_IDLE_CLASS =
  "text-sm px-3 py-1.5 rounded text-fg-muted hover:text-fg hover:bg-elev/70 transition-colors no-underline";

export const TogglesDivider = tw.div`
  ml-2 pl-3 border-l border-border-soft
  flex items-center gap-1
`;
