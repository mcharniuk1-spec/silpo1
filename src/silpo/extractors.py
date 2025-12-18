export type AppConfig = {
  categoryUrl: string;
  maxPages: number;
  tz: string;
  headless: boolean;

  sheetId: string;
  sheetDataName: string;
  sheetLogName: string;

  userAgent: string;
};

function mustGet(name: string): string {
  const v = process.env[name];
  if (!v || !v.trim()) throw new Error(`Missing env var: ${name}`);
  return v.trim();
}

export const CONFIG: AppConfig = {
  categoryUrl: process.env.CATEGORY_URL?.trim() || "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234",
  maxPages: Number(process.env.MAX_PAGES || "10"),
  tz: process.env.TZ?.trim() || "Europe/Kyiv",
  headless: (process.env.HEADLESS || "true").toLowerCase() !== "false",

  sheetId: mustGet("GOOGLE_SHEET_ID"),
  sheetDataName: "silpo_raw",
  sheetLogName: "silpo_log",

  // "browser-like" UA (але без будь-яких трюків обходу)
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
};

export const SERVICE_ACCOUNT_JSON = mustGet("GOOGLE_SERVICE_ACCOUNT_JSON");
