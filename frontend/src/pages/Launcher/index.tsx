import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  createRun,
  fetchModels,
  fetchSuites,
  type ModelInfo,
  type SuiteMeta,
} from "../../api";
import Alert from "../../components/Alert";
import { Primary } from "../../components/Button";
import PageHeader from "../../components/PageHeader";
import ModelsSelector from "./ModelsSelector";
import RuntimeFields from "./RuntimeFields";
import SuitesSelector from "./SuitesSelector";
import { FormStack, PageWrap, SubmitBar } from "./style";

export default function Launcher() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [suites, setSuites] = useState<SuiteMeta[]>([]);
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());
  const [selectedSuites, setSelectedSuites] = useState<Set<string>>(
    new Set(["baseline"])
  );
  const [numCtx, setNumCtx] = useState(8192);
  const [kvCache, setKvCache] = useState("f16");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [m, s] = await Promise.all([fetchModels(), fetchSuites()]);
        setModels(m);
        setSuites(s);
      } catch (e) {
        setErr(String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const toggle = (s: Set<string>, name: string, setter: (n: Set<string>) => void) => {
    const next = new Set(s);
    next.has(name) ? next.delete(name) : next.add(name);
    setter(next);
  };

  const canSubmit =
    selectedModels.size > 0 && selectedSuites.size > 0 && !submitting;

  const submit = async () => {
    setErr(null);
    setSubmitting(true);
    try {
      const run = await createRun({
        models: [...selectedModels],
        suites: [...selectedSuites],
        runtime_configs: [
          { num_ctx: numCtx, kv_cache_type: kvCache, temperature: 0, seed: 42, top_p: 1 },
        ],
        notes: notes || null,
      });
      navigate(`/runs/${run.id}`);
    } catch (e) {
      setErr(String(e));
      setSubmitting(false);
    }
  };

  return (
    <PageWrap>
      <PageHeader title={t("launcher.title")} subtitle={t("launcher.subtitle")} />

      {err && <Alert>{t("common.error")}: {err}</Alert>}

      {loading ? (
        <p className="text-fg-dim">{t("common.loading")}</p>
      ) : (
        <FormStack>
          <ModelsSelector
            models={models}
            selected={selectedModels}
            onToggle={(n) => toggle(selectedModels, n, setSelectedModels)}
          />
          <SuitesSelector
            suites={suites}
            selected={selectedSuites}
            onToggle={(n) => toggle(selectedSuites, n, setSelectedSuites)}
          />
          <RuntimeFields
            numCtx={numCtx}
            setNumCtx={setNumCtx}
            kvCache={kvCache}
            setKvCache={setKvCache}
            notes={notes}
            setNotes={setNotes}
          />
          <SubmitBar>
            <Primary onClick={submit} disabled={!canSubmit}>
              {submitting ? t("launcher.launching") : t("launcher.launch")}
            </Primary>
          </SubmitBar>
        </FormStack>
      )}
    </PageWrap>
  );
}
