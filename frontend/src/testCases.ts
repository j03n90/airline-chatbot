export type TestCase = {
  id: string;
  function: string;
  title: string;
  expected: string;
  starterMessage: string;
  seed?: {
    now_utc: string;
    bookings: unknown[];
  };
};

export const CUSTOM_CASE: TestCase = {
  id: "custom",
  function: "custom",
  title: "Custom / blank",
  expected: "Whatever seed you paste. Use this while debugging.",
  starterMessage: "",
};
