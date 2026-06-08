import { useTranslation } from "react-i18next";
import { NavLink, Outlet } from "react-router-dom";
import LanguageToggle from "../LanguageToggle";
import Logo from "../Logo";
import ThemeToggle from "../ThemeToggle";
import {
  BrandLink,
  BrandText,
  LayoutRoot,
  NAV_ACTIVE_CLASS,
  NAV_IDLE_CLASS,
  NavWrap,
  RightCluster,
  TogglesDivider,
  TopBar,
  TopBarInner,
} from "./style";

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? NAV_ACTIVE_CLASS : NAV_IDLE_CLASS;

export default function Layout() {
  const { t } = useTranslation();

  return (
    <LayoutRoot>
      <TopBar>
        <TopBarInner>
          <BrandLink to="/">
            <Logo size={50} />
            <BrandText>OLLAMPICS</BrandText>
          </BrandLink>
          <RightCluster>
            <NavWrap>
              <NavLink to="/" end className={navClass}>
                {t("nav.home")}
              </NavLink>
              <NavLink to="/dashboard" className={navClass}>
                {t("nav.dashboard")}
              </NavLink>
              <NavLink to="/launcher" className={navClass}>
                {t("nav.launcher")}
              </NavLink>
              <NavLink to="/leaderboard" className={navClass}>
                {t("nav.leaderboard")}
              </NavLink>
              <NavLink to="/tests" className={navClass}>
                {t("nav.tests")}
              </NavLink>
              <NavLink to="/compare" className={navClass}>
                {t("nav.compare")}
              </NavLink>
            </NavWrap>
            <TogglesDivider>
              <LanguageToggle />
              <ThemeToggle />
            </TogglesDivider>
          </RightCluster>
        </TopBarInner>
      </TopBar>
      <Outlet />
    </LayoutRoot>
  );
}
