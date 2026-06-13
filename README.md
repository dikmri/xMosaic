# xMosaic

xMosaic は、成人・同意済み・権利処理済み素材だけを対象にした、ローカル実行型の動画モザイクアプリです。

> xMosaic は、成人・同意済み・権利処理済み素材のみを対象にしています。
> 未成年または若年に見える人物、同意のない素材、流出・私的素材、違法素材、モザイク除去・復元用途には使用しないでください。

GUI は Electrobun で実装しています。動画処理コアは Python のまま維持し、Electrobun の WebView から Python worker をローカル実行します。ユーザー素材を外部送信しません。

## 機能

- Electrobun による軽量デスクトップ GUI
- ファイル選択ダイアログによる入力動画の選択
- 出力フォルダ選択と出力ファイル名編集
- FFmpeg による動画情報取得、フレーム抽出、再エンコード
- ピクセルモザイクと黒塗りレンダリング
- マスクの拡張、境界フェザー、時間方向スムージング
- 安全な E2E テスト用 `DummyDetector`
- HTML または JSON の品質確認レポート
- Python CLI による自動処理

## クイックスタート

詳しい手順は [クイックスタート](docs/QUICKSTART.md) を参照してください。

Windows でGUI版をインストールする場合は、PowerShellで次の1行を実行してください。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/dikmri/xMosaic/main/scripts/install.ps1 | iex"
```

インストール後はスタートメニューから `xMosaic` を起動できます。

## インストール

上の1行インストールは、最新リリースのWindows向けGUIインストーラーとPython workerを取得し、ローカル環境にセットアップします。PythonまたはFFmpegが見つからない場合は、利用可能な環境では `winget` で自動インストールします。

開発用チェックアウトから使う場合は、リポジトリのルートで次を実行します。

```powershell
python -m pip install -U pip
python -m pip install -e ".[dev]"
bun install
```

環境確認:

```bash
xmosaic doctor
```

## GUI の起動

```bash
bun run desktop:dev
```

Python CLI から起動する場合:

```bash
xmosaic gui
```

## CLI の使い方

```bash
xmosaic inspect input.mp4
xmosaic process input.mp4 -o output.mp4 --preset fanza-strong --detector dummy
xmosaic process input.mp4 -o output.mp4 --report report.html
```

現在の MVP で利用できる検出器は `dummy` のみです。YOLO セグメンテーション、SAM 2、ONNX Runtime バックエンドは後続フェーズで追加します。

## 開発チェック

```bash
ruff check src tests
pytest
bun run desktop:typecheck
bun run desktop:build
```

## 安全ポリシー

xMosaic は次の用途を拒否・禁止します。

- 未成年または若年に見える人物が含まれる素材
- 同意なく撮影・共有された素材
- 流出素材、私的素材、権利不明素材
- 違法素材
- モザイク除去、復元、逆モザイク用途
- ユーザー素材のクラウドアップロードまたは外部送信

公開リポジトリには、成人向けサンプル、成人向け学習済みモデル重み、権利不明データセットを含めません。

## ライセンス

ソースコードは MIT License で公開します。

モデル重みとデータセットは、ソースコードとは別の条件で配布される場合があります。
