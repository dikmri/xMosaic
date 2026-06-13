import type { ElectrobunConfig } from "electrobun";

export default {
  app: {
    name: "xMosaic",
    identifier: "jp.daikimarui.xmosaic",
    version: "0.1.0",
  },
  runtime: {
    exitOnLastWindowClosed: true,
  },
  build: {
    bun: {
      entrypoint: "desktop/bun/index.ts",
    },
    views: {
      main: {
        entrypoint: "desktop/view/index.ts",
        sourcemap: "linked",
      },
    },
    copy: {
      "desktop/view/index.html": "views/main/index.html",
      "desktop/view/styles.css": "views/main/styles.css",
    },
  },
} satisfies ElectrobunConfig;

