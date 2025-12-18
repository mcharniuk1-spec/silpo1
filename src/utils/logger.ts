export type LogLevel = "INFO" | "WARN" | "ERROR";

export type LogRow = {
  ts: string;
  level: LogLevel;
  step: string;
  stage: string;
  message: string;
  extra?: string;
};

export class RunLogger {
  private rows: LogRow[] = [];

  constructor(private tz: string) {}

  private nowIso(): string {
    // Keep it simple and stable for Sheets
    return new Date().toISOString();
  }

  log(level: LogLevel, step: string, stage: string, message: string, extra?: string) {
    const row: LogRow = { ts: this.nowIso(), level, step, stage, message, extra };
    this.rows.push(row);

    const line = `[${row.ts}] ${row.level} ${row.step} ${row.stage}: ${row.message}${row.extra ? " | " + row.extra : ""}`;
    // eslint-disable-next-line no-console
    console.log(line);
  }

  info(step: string, stage: string, message: string, extra?: string) {
    this.log("INFO", step, stage, message, extra);
  }
  warn(step: string, stage: string, message: string, extra?: string) {
    this.log("WARN", step, stage, message, extra);
  }
  error(step: string, stage: string, message: string, extra?: string) {
    this.log("ERROR", step, stage, message, extra);
  }

  getRows(): LogRow[] {
    return this.rows.slice();
  }
}
