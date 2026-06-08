import { useTranslation } from "react-i18next";
import Card from "../../../components/Card";
import {
  HeaderRow,
  TBody,
  TD,
  TDEmpty,
  TDMono,
  TDMuted,
  TDMutedRight,
  TDRight,
  TH,
  THCompact,
  THRight,
  THead,
  Table,
} from "../../../components/Table";
import type { LeaderboardEntry } from "../../../api";
import {
  BarFill,
  BarRow,
  BarText,
  BarTrack,
  RankDim,
  RankOrange,
  RankSky,
  RankYellow,
} from "./style";

const RANK = [RankYellow, RankSky, RankOrange];
const MEDALS = ["🥇", "🥈", "🥉"];

type Props = { entries: LeaderboardEntry[]; loading: boolean };

export default function LeaderboardTable({ entries, loading }: Props) {
  const { t } = useTranslation();

  return (
    <Card>
      <Table>
        <THead>
          <HeaderRow>
            <THCompact>{t("leaderboard.cols.rank")}</THCompact>
            <TH>{t("leaderboard.cols.model")}</TH>
            <TH>{t("leaderboard.cols.suite")}</TH>
            <TH>{t("leaderboard.cols.successRate")}</TH>
            <THRight>{t("leaderboard.cols.tps")}</THRight>
            <THRight>{t("leaderboard.cols.ttft")}</THRight>
            <THRight>{t("leaderboard.cols.tries")}</THRight>
            <THRight>{t("leaderboard.cols.vram")}</THRight>
          </HeaderRow>
        </THead>
        <TBody>
          {loading ? (
            <tr>
              <TDEmpty colSpan={8}>{t("common.loading")}</TDEmpty>
            </tr>
          ) : entries.length === 0 ? (
            <tr>
              <TDEmpty colSpan={8}>{t("leaderboard.empty")}</TDEmpty>
            </tr>
          ) : (
            entries.map((e, i) => {
              const RankCell = RANK[i] || RankDim;
              return (
                <tr
                  key={`${e.model}-${e.runtime_hash}-${e.suite}`}
                  className="border-t border-border-soft"
                >
                  <RankCell>{MEDALS[i] ?? i + 1}</RankCell>
                  <TDMono>{e.model}</TDMono>
                  <TDMuted>{e.suite}</TDMuted>
                  <TD>
                    <BarRow>
                      <BarTrack>
                        <BarFill style={{ width: `${e.success_rate * 100}%` }} />
                      </BarTrack>
                      <BarText>
                        {(e.success_rate * 100).toFixed(0)}% ({e.successes}/{e.n_tasks})
                      </BarText>
                    </BarRow>
                  </TD>
                  <TDRight>{e.avg_tps?.toFixed(1) ?? "—"}</TDRight>
                  <TDMutedRight>
                    {e.avg_ttft_ms ? `${Math.round(e.avg_ttft_ms)}` : "—"}
                  </TDMutedRight>
                  <TDMutedRight>{e.avg_tries.toFixed(1)}</TDMutedRight>
                  <TDMutedRight>
                    {e.peak_vram_mb ? `${(e.peak_vram_mb / 1024).toFixed(1)}G` : "—"}
                  </TDMutedRight>
                </tr>
              );
            })
          )}
        </TBody>
      </Table>
    </Card>
  );
}
