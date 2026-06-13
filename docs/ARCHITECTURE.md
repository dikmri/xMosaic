# xMosaic アーキテクチャ

```text
Electrobun GUI
  -> Bun main process
  -> Python worker JSON lines
  -> ffprobe によるメタデータ取得
  -> ffmpeg によるフレーム展開
  -> 検出器
  -> マスク拡張
  -> 時間方向スムージング
  -> モザイク描画
  -> ffmpeg による音声保持付き再エンコード
  -> QC レポート
```

MVP では `DummyDetector` をサポートします。これにより、成人向け素材やモデル重みなしで、動画パイプライン全体を安全にテストできます。

## 主要モジュール

- `xmosaic.cli`: Typer ベースの CLI
- `desktop/`: Electrobun GUI
- `xmosaic.electrobun_worker`: Electrobun から呼び出す JSON line worker
- `xmosaic.ffmpeg`: `ffmpeg` / `ffprobe` の薄い wrapper
- `xmosaic.pipeline`: 動画処理の全体制御
- `xmosaic.detection`: 検出器インターフェースと `DummyDetector`
- `xmosaic.mosaic`: マスク処理とモザイク描画
- `xmosaic.report`: QC レポート生成

## 配布と更新

GUI本体は Electrobun の `stable` ビルドとして配布します。リリースタグを push すると GitHub Actions が Windows、macOS、Linux の成果物と Python worker wheel を作成し、GitHub Releases へ添付します。

起動時には Electrobun Updater が GitHub Releases の latest download を確認し、新しいGUI本体があればダウンロード、適用、再起動します。Python worker はインストールスクリプトが専用venvへ配置し、GUIはOSごとの既定パスまたは `XMOSAIC_PYTHON` から検出します。

## 後続の拡張点

YOLO セグメンテーション、SAM 2、ONNX Runtime は後続フェーズで任意バックエンドとして追加します。未導入環境でも `DummyDetector` と基本 CLI は動く構成を維持します。
