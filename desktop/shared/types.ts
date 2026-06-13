import type { RPCSchema } from "electrobun";

export type VideoMetadata = {
  path: string;
  durationSeconds: number | null;
  durationLabel: string;
  fps: number | null;
  fpsLabel: string;
  width: number | null;
  height: number | null;
  resolution: string;
  videoCodec: string | null;
  audioCodec: string | null;
  formatName: string | null;
};

export type ProcessOptions = {
  preset: string;
  detector: string;
  device: string;
  confidenceThreshold: number;
  maskDilation: number;
  temporalSmoothing: number;
  reportPath: string | null;
  keepTemp: boolean;
};

export type ProcessProgressEvent = {
  type: "progress";
  stage: string;
  completed: number | null;
  total: number | null;
  message: string;
};

export type ProcessErrorEvent = {
  type: "error";
  message: string;
};

export type ProcessNoticeEvent = {
  type: "notice";
  message: string;
};

export type ProcessDoneEvent = {
  type: "done";
  outputPath: string;
  frameCount: number;
  qcIssues: number;
  reportPath: string | null;
};

export type ProcessEvent =
  | ProcessProgressEvent
  | ProcessErrorEvent
  | ProcessNoticeEvent
  | ProcessDoneEvent;

export type PathSuggestion = {
  inputPath: string;
  outputPath: string;
  reportPath: string;
};

export type InspectResult = {
  metadata: VideoMetadata;
};

export type ProcessResult = {
  outputPath: string;
  frameCount: number;
  qcIssues: number;
  reportPath: string | null;
};

export type XMosaicRPC = {
  bun: RPCSchema<{
    requests: {
      chooseInputVideo: {
        params: Record<string, never>;
        response: PathSuggestion | null;
      };
      chooseOutputFolder: {
        params: {
          inputPath: string;
          currentOutputPath: string;
        };
        response: string | null;
      };
      inspectVideo: {
        params: {
          inputPath: string;
        };
        response: InspectResult;
      };
      processVideo: {
        params: {
          inputPath: string;
          outputPath: string;
          options: ProcessOptions;
        };
        response: ProcessResult;
      };
      revealPath: {
        params: {
          path: string;
        };
        response: boolean;
      };
    };
    messages: {
      logToBun: {
        message: string;
      };
    };
  }>;
  webview: RPCSchema<{
    requests: Record<string, never>;
    messages: {
      processEvent: ProcessEvent;
    };
  }>;
};
