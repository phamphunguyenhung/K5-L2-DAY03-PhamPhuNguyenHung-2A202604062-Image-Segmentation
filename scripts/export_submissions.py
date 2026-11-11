"""Export job dataset từ CVAT local về submissions/<mã_task>.zip đúng format của task (không kèm ảnh gốc).

  python scripts/export_submissions.py [--only cp3_thin ...]

semantic -> "Segmentation mask 1.1"; instance/panoptic -> "COCO 1.0". Đọc CVAT_HOST, CVAT_PAT từ
biến môi trường (hoặc ../cvat-seg-copilot/.env). Chỉ đọc từ CVAT, không sửa annotation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
LAB = Path(__file__).resolve().parents[1]
FORMAT = {"semantic": "Segmentation mask 1.1", "instance": "COCO 1.0", "panoptic": "COCO 1.0"}


def load_env() -> None:
    env = LAB.parent / "cvat-seg-copilot" / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()
    load_env()
    from cvat_sdk import make_client

    manifest = json.loads((LAB / "data" / "manifest.json").read_text(encoding="utf-8"))["tasks"]
    out = LAB / "submissions"
    out.mkdir(exist_ok=True)
    with make_client(os.environ["CVAT_HOST"], credentials=None) as client:
        client.api_client.set_default_header("Authorization", f"Bearer {os.environ['CVAT_PAT'].strip()}")
        tasks = {t.name: t for t in client.tasks.list()}
        for name, meta in manifest.items():
            if a.only and name not in a.only:
                continue
            t = tasks.get(name)
            if not t:
                print(f"THIẾU  {name}: chưa có task")
                continue
            jobs = t.get_jobs()
            if len(jobs) != 1:
                print(f"LỖI    {name}: {len(jobs)} job, cần đúng 1")
                continue
            dest = out / f"{name}.zip"
            dest.unlink(missing_ok=True)  # bản export cũ của chính script này, ghi đè bằng bản mới
            jobs[0].export_dataset(FORMAT[meta["type"]], str(dest), include_images=False, status_check_period=2)
            print(f"OK     {name:<16} {FORMAT[meta['type']]:<22} -> {dest.name} ({dest.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
