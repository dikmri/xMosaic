# xMosaic Codex タスクリスト

## 実装済みの初期範囲

1. プロジェクト骨格
2. Typer による CLI
3. `doctor` コマンド
4. `inspect` コマンド
5. FFmpeg によるフレーム抽出と再エンコード
6. モザイクレンダラー
7. `DummyDetector`
8. `process` コマンドの E2E 処理
9. pytest
10. GitHub Actions

## 後続フェーズ

1. データセットパイプライン
2. YOLO セグメンテーションバックエンド
3. 任意機能としての SAM 2 バックエンド
4. 学習・ONNX export コマンド
5. リリース workflow の強化

## 厳守事項

- 公開リポジトリに成人向けサンプルメディアを含めない
- モザイク除去・復元機能を実装しない
- ユーザー素材をネットワーク送信しない
- ローカル処理を前提にする
- ソースコードは MIT License とする

