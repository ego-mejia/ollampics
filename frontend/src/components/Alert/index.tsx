import { AlertError } from "./style";

type Props = { children: React.ReactNode };

export default function Alert({ children }: Props) {
  return <AlertError role="alert">{children}</AlertError>;
}
