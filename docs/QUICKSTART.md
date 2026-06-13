# クイックスタート

このガイドでは、成人向け素材やモデル重みを使わず、`DummyDetector` で xMosaic の GUI と動画処理パイプラインを確認します。

## 1. 前提

- Windows、macOS、Linux のいずれか

Windows の利用者向け1行インストールでは、Python と FFmpeg が見つからない場合に `winget` での自動インストールを試みます。
開発用チェックアウトから実行する場合は、次のツールを事前に用意してください。

- Python 3.11 以上
- Bun
- FFmpeg と FFprobe

確認:

```bash
python --version
bun --version
ffmpeg -version
ffprobe -version
```

## 2. インストール

WindowsでGUI版をインストールする場合は、PowerShellで次の1行を実行します。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/dikmri/xMosaic/main/scripts/install.ps1 | iex"
```

開発用チェックアウトから使う場合は、リポジトリのルートで実行します。

```bash
python -m pip install -U pip
python -m pip install -e ".[dev]"
bun install
```

## 3. 環境確認

```bash
xmosaic doctor
```

`ffmpeg` と `ffprobe` が `ok` になっていれば、MVP の動画処理を実行できます。CUDA、MPS、モデルファイルは初期実装では必須ではありません。

## 4. Electrobun GUI を起動

```bash
bun run desktop:dev
```

または、Python CLI のランチャーから起動します。

```bash
xmosaic gui
```

GUI では次の操作を画面上で行えます。

- 入力動画の選択
- 出力フォルダの選択
- 出力ファイル名の編集
- QC レポートの保存先設定
- モザイクプリセットの選択
- `DummyDetector` による安全な E2E 処理
- 進捗とログの確認
- 処理後の出力ファイル表示

## 5. CLI で動画情報を確認

```bash
xmosaic inspect input.mp4
```

表示される主な項目:

- 再生時間
- FPS
- 解像度
- 音声 codec
- 映像 codec

## 6. CLI で DummyDetector 処理

```bash
xmosaic process input.mp4 -o output.mp4 --detector dummy --report report.html
```

`DummyDetector` はフレーム中央に矩形マスクを作る安全な検出器です。モデル重みや成人向けサンプルなしで、抽出、マスク処理、モザイク描画、再エンコード、レポート生成を確認できます。

## 7. プリセット

```bash
xmosaic process input.mp4 -o output.mp4 --preset light --detector dummy
xmosaic process input.mp4 -o output.mp4 --preset balanced --detector dummy
xmosaic process input.mp4 -o output.mp4 --preset fanza-strong --detector dummy
xmosaic process input.mp4 -o output.mp4 --preset black-box --detector dummy
```

## 8. 開発チェック

```bash
ruff check src tests
pytest
bun run desktop:typecheck
bun run desktop:build
```

テストでは無害な合成動画だけを生成します。公開リポジトリに成人向けサンプルやモデル重みを含めないでください。
