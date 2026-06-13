# モデル学習

モデル学習機能は後続フェーズで実装予定です。

このリポジトリにはモデル重みを含めません。学習済み重みを配布する場合は、ソースコードとは別の配布物として扱い、ライセンス、利用条件、学習データの由来、安全上の制限を明記します。

## 優先指標

xMosaic の用途では、見逃しを減らすことを重視します。

- Recall
- False Negative count
- Mask coverage
- Temporal stability
- Precision
- Processing speed

## 想定コマンド

```bash
xmosaic train \
  --dataset dataset_processed \
  --model yolo11n-seg.pt \
  --epochs 100 \
  --imgsz 1024 \
  --batch 8 \
  --device cuda
```

上記コマンドは現時点では未実装です。

