# データセット方針

このリポジトリにはデータセットを含めません。

利用できる素材は、成人・同意済み・権利処理済みで、適切なライセンスを持つものだけです。合成データを使う場合も、生成元、権利、実在人物を含まないこと、未成年または若年に見える人物を含まないことをメタデータで確認できる必要があります。

## 期待する入力構成

```text
dataset_raw/
├─ images/
├─ masks/
└─ metadata/
```

## 必須メタデータ例

```json
{
  "source": "ai_generated",
  "rights": "user_generated",
  "contains_real_person": false,
  "adult_only": true,
  "minor_or_youth_appearance": false,
  "consent_status": "synthetic",
  "classes": ["censor_region"]
}
```

## 拒否条件

- `minor_or_youth_appearance: true`
- `adult_only: false`
- `contains_real_person: true`
- 空のマスク
- 画像とマスクの対応欠落
- 権利や生成元を確認できない素材

