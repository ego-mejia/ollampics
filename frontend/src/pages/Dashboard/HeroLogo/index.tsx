import Logo from "../../../components/Logo";
import { HeroWrap } from "./style";

type Props = { size?: number };

export default function HeroLogo({ size = 300 }: Props) {
  return (
    <HeroWrap>
      <Logo size={size} ariaLabel="OLLAMPICS" />
    </HeroWrap>
  );
}
