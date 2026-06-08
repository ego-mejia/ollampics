import { useTranslation } from "react-i18next";
import HeroSection from "./HeroSection";
import HowToSection from "./HowToSection";
import MetricsSection from "./MetricsSection";
import { CTALink, PageWrap, Prose, Section, SectionTitle } from "./style";

export default function Home() {
  const { t } = useTranslation();
  return (
    <PageWrap>
      <HeroSection />

      <Section>
        <SectionTitle>{t("home.whatIsTitle")}</SectionTitle>
        <Prose>{t("home.whatIs1")}</Prose>
        <Prose>{t("home.whatIs2")}</Prose>
      </Section>

      <HowToSection />

      <MetricsSection />

      <Section>
        <SectionTitle>{t("home.addTestsTitle")}</SectionTitle>
        <Prose>{t("home.addTests1")}</Prose>
        <Prose>{t("home.addTests2")}</Prose>
      </Section>

      <Section>
        <SectionTitle>{t("home.addModelsTitle")}</SectionTitle>
        <Prose>{t("home.addModels1")}</Prose>
        <CTALink
          href="https://ollama.com/search"
          target="_blank"
          rel="noopener noreferrer"
        >
          {t("home.addModelsCTA")}
        </CTALink>
      </Section>
    </PageWrap>
  );
}
