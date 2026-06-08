import { useTranslation } from "react-i18next";
import SuiteIcon from "../../../components/SuiteIcon";
import { Section, SectionTitle } from "../style";
import {
  Step,
  StepBody,
  StepCode,
  StepIconWrap,
  StepLink,
  StepTitle,
  Steps,
  SuiteGrid,
  SuiteLabel,
  SuiteTile,
} from "./style";

const SUITES = ["baseline", "tool_calling", "rag", "planning", "personal_agent", "multi_agent"];

export default function HowToSection() {
  const { t } = useTranslation();
  return (
    <Section>
      <SectionTitle>{t("home.howTitle")}</SectionTitle>
      <Steps>
        <Step>
          <StepIconWrap>
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </StepIconWrap>
          <StepTitle>{t("home.howStep1Title")}</StepTitle>
          <StepBody>{t("home.howStep1")}</StepBody>
          <StepCode>{t("home.howStep1Code")}</StepCode>
          <StepLink
            href="https://ollama.com/search"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("home.howStep1CTA")} →
          </StepLink>
        </Step>
        <Step>
          <StepIconWrap>
            <SuiteIcon name="all" size={56} ariaLabel="suites" />
          </StepIconWrap>
          <StepTitle>{t("home.howStep2Title")}</StepTitle>
          <StepBody>{t("home.howStep2")}</StepBody>
          <SuiteGrid>
            {SUITES.map((s) => (
              <SuiteTile key={s}>
                <SuiteIcon name={s} size={28} ariaLabel={s} />
                <SuiteLabel>{t(`tests.suites.${s}.label`, s)}</SuiteLabel>
              </SuiteTile>
            ))}
          </SuiteGrid>
        </Step>
        <Step>
          <StepIconWrap>
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M3 3v18h18" />
              <rect x="6" y="12" width="3" height="6" />
              <rect x="11" y="8" width="3" height="10" />
              <rect x="16" y="4" width="3" height="14" />
            </svg>
          </StepIconWrap>
          <StepTitle>{t("home.howStep3Title")}</StepTitle>
          <StepBody>{t("home.howStep3")}</StepBody>
        </Step>
      </Steps>
    </Section>
  );
}
