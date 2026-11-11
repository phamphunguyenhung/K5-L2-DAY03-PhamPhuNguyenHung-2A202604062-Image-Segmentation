"""Tạo tự động task CVAT local từ data/manifest.json.

  python scripts/setup_cvat_tasks.py --check                 # lọc trước, không cần đăng nhập
  python scripts/setup_cvat_tasks.py [--only medium_instance]  # tạo task (bỏ qua task đã có)

Xác thực qua biến môi trường: CVAT_HOST (mặc định http://localhost:8080),
CVAT_PAT (Bearer) hoặc CVAT_USER + CVAT_PASS. Không hardcode bí mật.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
IMG_EXT = {".jpg", ".jpeg", ".png"}
EXPORT_FORMAT = {"semantic": "Segmentation mask 1.1", "instance": "COCO 1.0", "panoptic": "COCO 1.0"}


def load_plan() -> list[dict]:
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    plan = []
    for name, meta in manifest["tasks"].items():
        folder = DATA / meta["path"]
        labels = json.loads((folder / "cvat-labels.json").read_text(encoding="utf-8"))
        classes = json.loads((folder / "classes.json").read_text(encoding="utf-8"))
        images = sorted(p for p in (folder / "images").iterdir() if p.suffix.lower() in IMG_EXT)
        plan.append({"name": name, "type": meta["type"], "labels": labels, "classes": classes, "images": images})
    return plan


def check(plan: list[dict]) -> int:
    bad = 0
    for t in plan:
        names = [l["name"] for l in t["labels"]]
        missing = [c for c in t["classes"]["classes"] if c not in names]
        ok = bool(t["images"]) and bool(names) and len(set(names)) == len(names) and not missing
        bad += not ok
        print(f"{'OK ' if ok else 'ERR'} {t['name']:<16} {t['type']:<9} imgs={len(t['images'])} labels={len(names)} "
              f"export={EXPORT_FORMAT[t['type']]}" + (f" missing={missing}" if missing else ""))
    return bad


def create(plan: list[dict], only: set[str]) -> None:
    from cvat_sdk import make_client
    from cvat_sdk.core.proxies.tasks import ResourceType

    host = os.environ.get("CVAT_HOST", "http://localhost:8080")
    user, pw, pat = os.environ.get("CVAT_USER"), os.environ.get("CVAT_PASS"), os.environ.get("CVAT_PAT")
    if not (pat or (user and pw)):
        sys.exit("Thiếu CVAT_PAT hoặc CVAT_USER + CVAT_PASS trong môi trường.")
    with make_client(host, credentials=None if pat else (user, pw)) as client:
        if pat:
            client.api_client.set_default_header("Authorization", f"Bearer {pat.strip()}")
        existing = {t.name for t in client.tasks.list()}
        for t in plan:
            if only and t["name"] not in only:
                continue
            if t["name"] in existing:
                print(f"SKIP {t['name']} (đã có)")
                continue
            task = client.tasks.create_from_data(
                spec={"name": t["name"], "labels": t["labels"]},
                resource_type=ResourceType.LOCAL,
                resources=[str(p) for p in t["images"]],
            )
            print(f"NEW  {t['name']} id={task.id} jobs={[j.id for j in task.get_jobs()]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", nargs="*", default=[], help="chỉ tạo các task này")
    args = ap.parse_args()
    plan = load_plan()
    if args.check:
        sys.exit(1 if check(plan) else 0)
    create(plan, set(args.only))
1
