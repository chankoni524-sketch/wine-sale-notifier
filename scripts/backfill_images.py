import json
from pathlib import Path

from image_utils import fetch_og_image

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DATA_FILES = [
    DOCS_DIR / "data.json",
    DOCS_DIR / "festivals.json",
    DOCS_DIR / "menus.json",
    DOCS_DIR / "local_news.json",
]


def main():
    for path in DATA_FILES:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for key, item in data.items():
            if item.get("image_url"):
                continue
            url = item.get("url")
            if not url:
                continue
            image_url = fetch_og_image(url)
            if image_url:
                item["image_url"] = image_url
                changed = True
                print(f"{path.name}: {key} -> {image_url}")
        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{path.name} を更新しました")
        else:
            print(f"{path.name} は変更なし")


if __name__ == "__main__":
    main()
