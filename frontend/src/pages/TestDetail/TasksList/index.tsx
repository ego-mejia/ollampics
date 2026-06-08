import { useTranslation } from "react-i18next";
import Card from "../../../components/Card";
import { SectionTitle } from "../../../components/PageHeader";
import type { SuiteDetail } from "../../../api";
import { Row, Section, TaskDesc, TaskId, Triesmall } from "./style";

type Props = { detail: SuiteDetail };

export default function TasksList({ detail }: Props) {
  const { t } = useTranslation();
  if (detail.tasks.length === 0) return null;
  return (
    <Section>
      <SectionTitle>
        {t("tests.tasksInSuite")} ({detail.tasks.length})
      </SectionTitle>
      <Card>
        <div className="px-4">
          {detail.tasks.map((task) => (
            <Row key={task.task_id}>
              <div>
                <TaskId>{task.task_id}</TaskId>
                {task.description && <TaskDesc>{task.description}</TaskDesc>}
              </div>
              <Triesmall>max {task.max_tries} tries · v{task.version}</Triesmall>
            </Row>
          ))}
        </div>
      </Card>
    </Section>
  );
}
