#!/usr/bin/env python3
"""
Download the NCFC daily report PDF and save it to the Downloads folder (or a custom folder).

Usage:
  python3 scripts/download_report.py
  python3 scripts/download_report.py --to /path/to/dir
  python3 scripts/download_report.py --url <url> --name BaseName

The script defaults to ~/Downloads and names the file:
  LatestAgriculturalCondAsses_YYYY-MM-DD.pdf

Exits with code 0 on success, non-zero on failure.
"""
from __future__ import annotations
import argparse
import datetime
import os
import sys
import urllib.request
import urllib.error
import time

URL = "https://www.ncfc.gov.in/downloads/LatestAgriculturalCondAsses.pdf"
DEFAULT_NAME = "LatestAgriculturalCondAsses"

def download_pdf(url: str, out_path: str, timeout: int = 20, retries: int = 2, backoff: float = 1.5) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "ncfc-downloader/1.0"})
    last_exc = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", None)
                if status is not None and status >= 400:
                    raise RuntimeError(f"HTTP error: {status}")
                content_type = resp.getheader("Content-Type") or ""
                if "pdf" not in content_type.lower():
                    # warn but allow; sometimes servers misreport content-type
                    print(f"Warning: unexpected Content-Type: {content_type}")
                data = resp.read()
                if not data:
                    raise RuntimeError("Downloaded file is empty")
                # write to temp file first then move
                tmp = out_path + ".part"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, out_path)
                return
        except Exception as e:
            last_exc = e
            if attempt < retries:
                wait = backoff * (2 ** attempt)
                print(f"Attempt {attempt+1} failed: {e!r}. Retrying in {wait:.1f}s...")
                time.sleep(wait)
            else:
                raise
    raise last_exc

def make_filename(base_name: str, date: datetime.date) -> str:
    return f"{base_name}_{date.isoformat()}.pdf"

def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Download NCFC LatestAgriculturalCondAsses.pdf and save with today's date")
    p.add_argument("--to", "-t", dest="to", default=None, help="Target directory (default: ~/Downloads)")
    p.add_argument("--url", dest="url", default=URL, help="PDF URL (default: the NCFC report)")
    p.add_argument("--name", dest="name", default=DEFAULT_NAME, help="Base filename (default: LatestAgriculturalCondAsses)")
    p.add_argument("--retries", dest="retries", type=int, default=2, help="Number of retries on failure (default 2)")
    args = p.parse_args(argv)

    target_dir = args.to or os.path.expanduser("~/Downloads")
    target_dir = os.path.abspath(target_dir)
    os.makedirs(target_dir, exist_ok=True)

    today = datetime.date.today()
    filename = make_filename(args.name, today)
    out_path = os.path.join(target_dir, filename)

    print(f"Downloading {args.url} to {out_path} ...")
    try:
        download_pdf(args.url, out_path, retries=args.retries)
    except Exception as e:
        print(f"Failed to download: {e}")
        return 2

    # Basic verification
    try:
        size = os.path.getsize(out_path)
    except OSError:
        print("Failed to stat downloaded file")
        return 3
    if size == 0:
        print("Downloaded file is zero bytes")
        return 4

    print(f"Success: saved {out_path} ({size} bytes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
