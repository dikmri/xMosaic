import { Electroview } from "electrobun/view";

import type { ProcessEvent, ProcessOptions, XMosaicRPC } from "../shared/types";

const rpc = Electroview.defineRPC<XMosaicRPC>({
  handlers: {
    messages: {
      processEvent: (event) => handleProcessEvent(event),
    },
  },
});

const electrobun = new Electroview({ rpc });

const state: {
  inputPath: string;
  outputPath: string;
  reportPath: string;
  running: boolean;
  lastOutputPath: string;
} = {
  inputPath: "",
  outputPath: "",
  reportPath: "",
  running: false,
  lastOutputPath: "",
};

const inputLabel = byId("inputLabel", HTMLElement);
const outputPathInput = byId("outputPathInput", HTMLInputElement);
const reportPathInput = byId("reportPathInput", HTMLInputElement);
const reportEnabledInput = byId("reportEnabledInput", HTMLInputElement);
const presetInput = byId("presetInput", HTMLSelectElement);
const detectorInput = byId("detectorInput", HTMLSelectElement);
const deviceInput = byId("deviceInput", HTMLSelectElement);
const confidenceInput = byId("confidenceInput", HTMLInputElement);
const dilationInput = byId("dilationInput", HTMLInputElement);
const smoothingInput = byId("smoothingInput", HTMLInputElement);
const keepTempInput = byId("keepTempInput", HTMLInputElement);
const statusLabel = byId("statusLabel", HTMLElement);
const progressBar = byId("progressBar", HTMLProgressElement);
const runButton = byId("runButton", HTMLButtonElement);
const revealButton = byId("revealButton", HTMLButtonElement);
const inspectButton = byId("inspectButton", HTMLButtonElement);
const logList = byId("logList", HTMLOListElement);

byId("chooseInputButton", HTMLButtonElement).addEventListener("click", chooseInputVideo);
byId("chooseOutputButton", HTMLButtonElement).addEventListener("click", chooseOutputFolder);
runButton.addEventListener("click", runProcess);
inspectButton.addEventListener("click", inspectVideo);
revealButton.addEventListener("click", revealOutput);

outputPathInput.addEventListener("input", () => {
  state.outputPath = outputPathInput.value.trim();
});
reportPathInput.addEventListener("input", () => {
  state.reportPath = reportPathInput.value.trim();
});

function byId<T extends typeof HTMLElement>(id: string, expected: T): InstanceType<T> {
  const element = document.getElementById(id);
  if (!(element instanceof expected)) {
    throw new Error(`missing element: ${id}`);
  }
  return element as InstanceType<T>;
}

async function chooseInputVideo(): Promise<void> {
  const result = await electrobun.rpc!.request.chooseInputVideo({});
  if (!result) {
    return;
  }
  state.inputPath = result.inputPath;
  state.outputPath = result.outputPath;
  state.reportPath = result.reportPath;
  inputLabel.textContent = result.inputPath;
  outputPathInput.value = result.outputPath;
  reportPathInput.value = result.reportPath;
  progressBar.value = 0;
  setStatus("動画を選択しました");
  appendLog("入力動画を選択しました");
}

async function chooseOutputFolder(): Promise<void> {
  const outputPath = await electrobun.rpc!.request.chooseOutputFolder({
    inputPath: state.inputPath,
    currentOutputPath: state.outputPath,
  });
  if (!outputPath) {
    return;
  }
  state.outputPath = outputPath;
  outputPathInput.value = outputPath;
  appendLog("出力フォルダを更新しました");
}

async function inspectVideo(): Promise<void> {
  if (!state.inputPath) {
    setStatus("入力動画を選択してください");
    return;
  }
  try {
    const result = await electrobun.rpc!.request.inspectVideo({ inputPath: state.inputPath });
    const m = result.metadata;
    appendLog(
      `動画情報: ${m.durationLabel}, ${m.fpsLabel} fps, ${m.resolution}, video=${m.videoCodec ?? "不明"}, audio=${m.audioCodec ?? "なし"}`,
    );
    setStatus("動画情報を取得しました");
  } catch (error) {
    showError(error);
  }
}

async function runProcess(): Promise<void> {
  if (!state.inputPath) {
    setStatus("入力動画を選択してください");
    return;
  }
  state.outputPath = outputPathInput.value.trim();
  state.reportPath = reportPathInput.value.trim();
  if (!state.outputPath) {
    setStatus("出力動画を指定してください");
    return;
  }

  setRunning(true);
  progressBar.value = 0;
  appendLog("処理を開始しました");
  setStatus("開始しています");

  try {
    const result = await electrobun.rpc!.request.processVideo({
      inputPath: state.inputPath,
      outputPath: state.outputPath,
      options: collectOptions(),
    });
    state.lastOutputPath = result.outputPath;
    revealButton.disabled = false;
    appendLog(`完了: ${result.outputPath}`);
    appendLog(`フレーム: ${result.frameCount}, QC: ${result.qcIssues}`);
    setStatus("完了しました");
    progressBar.value = 100;
  } catch (error) {
    showError(error);
  } finally {
    setRunning(false);
  }
}

function collectOptions(): ProcessOptions {
  const reportPath = reportEnabledInput.checked ? state.reportPath || null : null;
  return {
    preset: presetInput.value,
    detector: detectorInput.value,
    device: deviceInput.value,
    confidenceThreshold: Number(confidenceInput.value),
    maskDilation: Number(dilationInput.value),
    temporalSmoothing: Number(smoothingInput.value),
    reportPath,
    keepTemp: keepTempInput.checked,
  };
}

function handleProcessEvent(event: ProcessEvent): void {
  if (event.type === "progress") {
    setStatus(event.message);
    appendLog(event.message);
    if (event.completed !== null && event.total) {
      progressBar.value = Math.round((event.completed / event.total) * 100);
    }
    return;
  }
  if (event.type === "done") {
    state.lastOutputPath = event.outputPath;
    revealButton.disabled = false;
    setStatus("完了しました");
    progressBar.value = 100;
    return;
  }
  showError(event.message);
}

async function revealOutput(): Promise<void> {
  if (!state.lastOutputPath) {
    return;
  }
  await electrobun.rpc!.request.revealPath({ path: state.lastOutputPath });
}

function setRunning(running: boolean): void {
  state.running = running;
  runButton.disabled = running;
  inspectButton.disabled = running;
}

function setStatus(message: string): void {
  statusLabel.textContent = message;
}

function appendLog(message: string): void {
  const item = document.createElement("li");
  item.textContent = message;
  logList.append(item);
  while (logList.children.length > 120) {
    logList.firstElementChild?.remove();
  }
  item.scrollIntoView({ block: "nearest" });
}

function showError(error: unknown): void {
  const message = error instanceof Error ? error.message : String(error);
  setStatus(message);
  appendLog(`エラー: ${message}`);
}
