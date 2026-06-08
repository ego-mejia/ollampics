import { useTranslation } from "react-i18next";
import { LangBtn } from "./style";

export default function LanguageToggle() {
  const { i18n, t } = useTranslation();
  const current = i18n.language?.startsWith("es") ? "es" : "en";
  const next = current === "en" ? "es" : "en";
  const label = next === "es" ? t("lang.spanish") : t("lang.english");

  return (
    <LangBtn
      onClick={() => i18n.changeLanguage(next)}
      aria-label={t("lang.switchTo", { name: label })}
      title={t("lang.switchTo", { name: label })}
    >
      {current}
    </LangBtn>
  );
}
