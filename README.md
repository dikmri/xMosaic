# xMosaic

xMosaic は、成人・同意済み・権利処理済み素材だけを対象にした、ローカル実行型の動画モザイク CLI です。

> xMosaic は、成人・同意済み・権利処理済み素材のみを対象にしています。
> 未成年または若年に見える人物、同意のない素材、流出・私的素材、違法素材、モザイク除去・復元用途には使用しないでください。

最初の実装では `DummyDetector` を同梱しています。成人向けサンプル、モデル重み、ネットワーク送信なしで、動画処理パイプライン全体を安全に検証できます。

## 機能

- ローカル完結の動画処理
- FFmpeg による動画情報取得、フレーム抽出、再エンコード
- ピクセルモザイクと黒塗りレンダリング
- マスクの拡張、境界フェザー、時間方向スムージング
- 安全な E2E テスト用 `DummyDetector`
- HTML または JSON の品質確認レポート
- Windows / macOS / Linux 向け Python CLI

## クイックスタート

詳しい手順は [クイックスタート](docs/QUICKSTART.md) を参照してください。

```bash
python -m pip install -e ".[dev]"
xmosaic doctor
xmosaic inspect input.mp4
xmosaic process input.mp4 -o output.mp4 --detector dummy --report report.html
```

## インストール

公開パッケージとして配布後は次の形式で導入できます。

```bash
pipx install xmosaic
xmosaic doctor
```

開発用チェックアウトから使う場合:

```bash
python -m pip install -e ".[dev]"
xmosaic doctor
```

## 使い方

```bash
xmosaic inspect input.mp4
xmosaic process input.mp4 -o output.mp4 --preset fanza-strong --detector dummy
xmosaic process input.mp4 -o output.mp4 --report report.html
```

現在の MVP で利用できる検出器は `dummy` のみです。YOLO セグメンテーション、SAM 2、ONNX Runtime バックエンドは後続フェーズで追加します。

## 安全ポリシー

xMosaic は次の用途を拒否・禁止します。

- 未成年または若年に見える人物が含まれる素材
- 同意なく撮影・共有された素材
- 流出素材、私的素材、権利不明素材
- 違法素材
- モザイク除去、復元、逆モザイク用途
- ユーザー素材のクラウドアップロードまたは外部送信

公開リポジトリには、成人向けサンプル、成人向け学習済みモデル重み、権利不明データセットを含めません。

## 開発

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
pytest
ruff check src tests
```

## ライセンス

ソースコードは MIT License で公開します。

モデル重みとデータセットは、ソースコードとは別の条件で配布される場合があります。

