from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> None:
    root = project_root()
    package_json = root / "package.json"
    bun = shutil.which("bun")
    if bun is None:
        raise SystemExit(
            "Bun が見つかりません。https://bun.sh/ から Bun をインストールしてください。"
        )
    if not package_json.exists():
        raise SystemExit(
            "Electrobun GUI はソースチェックアウトから起動してください。"
            " リポジトリのルートで `bun run desktop:dev` を実行できます。"
        )
    raise SystemExit(subprocess.call([bun, "run", "desktop:dev"], cwd=root))


if __name__ == "__main__":
    main()
