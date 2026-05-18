import { type FormControlState } from "./FormControlContext.js";
type FormControlStateKey = keyof FormControlState;
type FormControlStateResult<Props, States extends readonly FormControlStateKey[]> = { [State in States[number]]: State extends keyof Props ? Props[State] | FormControlState[State] : FormControlState[State] };
export default function useFormControl(): FormControlState | undefined;
export declare function useFormControlState<Props, States extends readonly FormControlStateKey[]>({
  props,
  states
}: {
  props: Props;
  states: States;
}): [FormControlStateResult<Props, States>, FormControlState | undefined];
export {};