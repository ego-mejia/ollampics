import {
  HeaderWrap,
  PageTitle,
  SectionTitle,
  Subtitle,
  TitleBlock,
} from "./style";

type Props = {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
};

export default function PageHeader({ title, subtitle, actions }: Props) {
  return (
    <HeaderWrap>
      <TitleBlock>
        <PageTitle>{title}</PageTitle>
        {subtitle && <Subtitle>{subtitle}</Subtitle>}
      </TitleBlock>
      {actions}
    </HeaderWrap>
  );
}

export { SectionTitle };
