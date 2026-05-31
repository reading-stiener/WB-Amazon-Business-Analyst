import shutil
from pathlib import Path

import kagglehub

DEST = Path(__file__).parent / "data" / "brazilian-ecommerce"
DEST.mkdir(parents=True, exist_ok=True)

cached = Path(kagglehub.dataset_download("olistbr/brazilian-ecommerce"))

for item in cached.iterdir():
    target = DEST / item.name
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    shutil.copy2(item, target) if item.is_file() else shutil.copytree(item, target)

print("Dataset copied to:", DEST)