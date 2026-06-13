import { existsSync } from "node:fs";
import { basename, dirname, join, parse, resolve, sep } from "node:path";

import { BrowserView, BrowserWindow, Screen, Utils } from "electrobun/bun";

import type {
  InspectResult,
  PathSuggestion,
  ProcessEvent,
  ProcessOptions,
  ProcessResult,
  XMosaicRPC,
} from "../shared/types";

type WorkerJson =
  | { type: "result"; [key: string]: unknown }
  | {
      type: "progress";
      stage: string;
      completed: number | null;
      total: number | null;
      message: string;
    }
  | { type: "error"; message: string };

const repoRoot = resolve(process.cwd());
const python = resolvePython();
let processing = false;

const rpc = BrowserView.defineRPC<XMosaicRPC>({
  maxRequestTime: 1000 * 60 * 60 * 6,
  handlers: {
    requests: {
      chooseInputVideo: async () => {
        const chosen = await Utils.openFileDialog({
          startingFolder: Utils.paths.videos,
          allowedFileTypes: "mp4,mov,mkv,webm",
          canChooseFiles: true,
          canChooseDirectory: false,
          allowsMultipleSelection: false,
        });
        const inputPath = normalizeDialogPath(chosen);
        if (!inputPath) {
          return null;
        }
        return suggestPaths(inputPath);
      },
      chooseOutputFolder: async ({ inputPath, currentOutputPath }) => {
        const startingFolder = currentOutputPath
          ? dirname(currentOutputPath)
          : inputPath
            ? dirname(inputPath)
            : Utils.paths.videos;
        const chosen = await Utils.openFileDialog({
          startingFolder,
          allowedFileTypes: "*",
          canChooseFiles: false,
          canChooseDirectory: true,
          allowsMultipleSelection: false,
        });
        const folder = normalizeDialogPath(chosen);
        if (!folder) {
          return null;
        }
        const outputName = currentOutputPath
          ? basename(currentOutputPath)
          : basename(suggestPaths(inputPath).outputPath);
        return join(folder, outputName);
      },
      inspectVideo: async ({ inputPath }) => {
        return (await runWorkerResult(["inspect", inputPath])) as InspectResult;
      },
      processVideo: async ({ inputPath, outputPath, options }) => {
        if (processing) {
          throw new Error("別の処理が実行中です。");
        }
        processing = true;
        try {
          return await processWithWorker(inputPath, outputPath, options);
        } finally {
          processing = false;
        }
      },
      revealPath: ({ path }) => {
        if (!path) {
          return false;
        }
        Utils.showItemInFolder(path);
        return true;
      },
    },
    messages: {
      logToBun: ({ message }) => {
        console.log(`[view] ${message}`);
      },
    },
  },
});

let mainWindow: BrowserWindow<typeof rpc> | null = null;

const primary = Screen.getPrimaryDisplay();
const width = Math.min(1180, Math.max(980, primary.workArea.width - 120));
const height = Math.min(780, Math.max(680, primary.workArea.height - 100));
const x = Math.round(primary.workArea.x + (primary.workArea.width - width) / 2);
const y = Math.round(primary.workArea.y + (primary.workArea.height - height) / 2);

mainWindow = new BrowserWindow<typeof rpc>({
  title: "xMosaic",
  url: "views://main/index.html",
  frame: { x, y, width, height },
  titleBarStyle: "default",
  rpc,
});

function resolvePython(): string {
  const candidates = [process.env.XMOSAIC_PYTHON, "python", "python3"].filter(
    Boolean,
  ) as string[];
  for (const candidate of candidates) {
    try {
      const probe = Bun.spawnSync({
        cmd: [candidate, "--version"],
        stdout: "pipe",
        stderr: "pipe",
      });
      if (probe.exitCode === 0) {
        return candidate;
      }
    } catch {
      // Try the next candidate.
    }
  }
  return candidates[0] ?? "python";
}

function workerEnv(): Record<string, string> {
  const pathSeparator = process.platform === "win32" ? ";" : ":";
  const srcPath = join(repoRoot, "src");
  return {
    ...process.env,
    PYTHONPATH: process.env.PYTHONPATH ? `${srcPath}${pathSeparator}${process.env.PYTHONPATH}` : srcPath,
    PYTHONUTF8: "1",
  };
}

function normalizeDialogPath(value: unknown): string | null {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value) && typeof value[0] === "string") {
    return value[0];
  }
  return null;
}

function suggestPaths(inputPath: string): PathSuggestion {
  const parsed = parse(inputPath);
  const extension = parsed.ext || ".mp4";
  const outputPath = join(parsed.dir, `${parsed.name}_xmosaic${extension}`);
  const reportPath = join(parsed.dir, `${parsed.name}_xmosaic_report.html`);
  return { inputPath, outputPath, reportPath };
}

async function runWorkerResult(args: string[]): Promise<Record<string, unknown>> {
  const events = await runWorker(args);
  const error = events.find((event) => event.type === "error") as { message: string } | undefined;
  if (error) {
    throw new Error(error.message);
  }
  const result = events.find((event) => event.type === "result");
  if (!result) {
    throw new Error("Python worker から結果を取得できませんでした。");
  }
  return result as Record<string, unknown>;
}

async function processWithWorker(
  inputPath: string,
  outputPath: string,
  options: ProcessOptions,
): Promise<ProcessResult> {
  const args = [
    "process",
    "--input",
    inputPath,
    "--output",
    outputPath,
    "--preset",
    options.preset,
    "--detector",
    options.detector,
    "--device",
    options.device,
    "--confidence-threshold",
    String(options.confidenceThreshold),
    "--mask-dilation",
    String(options.maskDilation),
    "--temporal-smoothing",
    String(options.temporalSmoothing),
  ];
  if (options.reportPath) {
    args.push("--report", options.reportPath);
  }
  if (options.keepTemp) {
    args.push("--keep-temp");
  }

  const events = await runWorker(args, (event) => {
    if (event.type === "progress") {
      sendToView({
        type: "progress",
        stage: event.stage,
        completed: event.completed,
        total: event.total,
        message: event.message,
      });
    }
  });
  const error = events.find((event) => event.type === "error") as { message: string } | undefined;
  if (error) {
    sendToView({ type: "error", message: error.message });
    throw new Error(error.message);
  }

  const result = events.find((event) => event.type === "result") as
    | { outputPath: string; report?: { frame_count?: number; low_confidence_frames?: unknown[] } }
    | undefined;
  if (!result) {
    throw new Error("Python worker から処理結果を取得できませんでした。");
  }
  const frameCount = Number(result.report?.frame_count ?? 0);
  const qcIssues = Array.isArray(result.report?.low_confidence_frames)
    ? result.report.low_confidence_frames.length
    : 0;
  const done = {
    type: "done",
    outputPath: result.outputPath,
    frameCount,
    qcIssues,
    reportPath: options.reportPath,
  } satisfies ProcessEvent;
  sendToView(done);
  Utils.showNotification({
    title: "xMosaic",
    body: "動画処理が完了しました。",
    silent: true,
  });
  return {
    outputPath: result.outputPath,
    frameCount,
    qcIssues,
    reportPath: options.reportPath,
  };
}

async function runWorker(
  args: string[],
  onEvent?: (event: WorkerJson) => void,
): Promise<WorkerJson[]> {
  if (!existsSync(join(repoRoot, "src", "xmosaic"))) {
    throw new Error(`xMosaic の Python ソースが見つかりません: ${repoRoot}${sep}src`);
  }

  const proc = Bun.spawn({
    cmd: [python, "-m", "xmosaic.electrobun_worker", ...args],
    cwd: repoRoot,
    env: workerEnv(),
    stdout: "pipe",
    stderr: "pipe",
  });

  const events: WorkerJson[] = [];
  const stdoutPromise = readJsonLines(proc.stdout, (event) => {
    events.push(event);
    onEvent?.(event);
  });
  const stderrPromise = readText(proc.stderr);
  const exitCode = await proc.exited;
  await stdoutPromise;
  const stderr = (await stderrPromise).trim();
  if (stderr) {
    console.warn(stderr);
  }
  if (exitCode !== 0 && !events.some((event) => event.type === "error")) {
    throw new Error(stderr || `Python worker が終了コード ${exitCode} で停止しました。`);
  }
  return events;
}

async function readJsonLines(
  stream: ReadableStream<Uint8Array>,
  onEvent: (event: WorkerJson) => void,
): Promise<void> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    let newline = buffer.indexOf("\n");
    while (newline !== -1) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (line) {
        onEvent(JSON.parse(line) as WorkerJson);
      }
      newline = buffer.indexOf("\n");
    }
  }
  buffer += decoder.decode();
  const rest = buffer.trim();
  if (rest) {
    onEvent(JSON.parse(rest) as WorkerJson);
  }
}

async function readText(stream: ReadableStream<Uint8Array>): Promise<string> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let text = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    text += decoder.decode(value, { stream: true });
  }
  return text + decoder.decode();
}

function sendToView(event: ProcessEvent): void {
  mainWindow?.webview.rpc?.send.processEvent(event);
}
