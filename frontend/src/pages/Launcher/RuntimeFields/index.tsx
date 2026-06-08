import { useTranslation } from "react-i18next";
import {
  Field,
  FieldLabel,
  NumberInput,
  Row,
  Select,
  TextInput,
} from "./style";

const KV_OPTIONS = ["f16", "q8_0", "q4_0"];

type Props = {
  numCtx: number;
  setNumCtx: (n: number) => void;
  kvCache: string;
  setKvCache: (s: string) => void;
  notes: string;
  setNotes: (s: string) => void;
};

export default function RuntimeFields({
  numCtx,
  setNumCtx,
  kvCache,
  setKvCache,
  notes,
  setNotes,
}: Props) {
  const { t } = useTranslation();
  return (
    <>
      <Row>
        <Field>
          <FieldLabel>{t("launcher.numCtx")}</FieldLabel>
          <NumberInput
            type="number"
            value={numCtx}
            onChange={(e) => setNumCtx(Number(e.target.value))}
            step={1024}
            min={512}
            max={131072}
          />
        </Field>
        <Field>
          <FieldLabel>{t("launcher.kvCache")}</FieldLabel>
          <Select value={kvCache} onChange={(e) => setKvCache(e.target.value)}>
            {KV_OPTIONS.map((opt) => (
              <option key={opt}>{opt}</option>
            ))}
          </Select>
        </Field>
      </Row>
      <section>
        <FieldLabel>{t("launcher.notes")}</FieldLabel>
        <TextInput
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={t("launcher.notesPlaceholder")}
        />
      </section>
    </>
  );
}
