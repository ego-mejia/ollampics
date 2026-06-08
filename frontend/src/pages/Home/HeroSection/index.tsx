import { useTranslation } from "react-i18next";
import Logo from "../../../components/Logo";
import { CTAGroup, CTARouterLink, CTASecondary } from "../style";
import { LogoSlot, Subtitle, Tagline, Wrap } from "./style";

export default function HeroSection() {
  const { t } = useTranslation();
  return (
    <Wrap>
      <LogoSlot>
        <Logo size={280} ariaLabel="OLLAMPICS" />
      </LogoSlot>
      <Tagline>{t("home.heroTagline")}</Tagline>
      <Subtitle>{t("home.heroSubtitle")}</Subtitle>
      <CTAGroup>
        <CTARouterLink to="/launcher">{t("home.ctaLaunch")}</CTARouterLink>
        <CTASecondary to="/dashboard">{t("home.ctaDashboard")}</CTASecondary>
      </CTAGroup>
    </Wrap>
  );
}
