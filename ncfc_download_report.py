#!/usr/bin/env python3
"""
Download the NCFC daily report PDF and save it to a target folder.

Usage:
  python scripts/download_report.py
  python scripts/download_report.py --to /path/to/dir
  python scripts/download_report.py --url <url> --name BaseName

Defaults:
  target dir: ~/Downloads
  filename: LatestAgriculturalCondAsses_YYYY-MM-DD.pdf
"""
from __future__ import annotations
import argparse
import datetime
import os
import sys
import time

URL_DEFAULT = "https://www.ncfc.gov.in/downloads/LatestAgriculturalCondAsses.pdf"
DEFAULT_NAME = "LatestAgriculturalCondAsses"

# Browser-like headers to avoid simple UA blocking
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/octet-stream,application/*;q=0.9,*/*;q=0.8",
    "Referer": "https://www.ncfc.gov.in/",
}


def make_filename(base_name: str, date: datetime.date) -> str:
    return f"{base_name}_{date.isoformat()}.pdf"


def download_with_requests(url: str, out_path: str, headers: dict, timeout: int = 20, stream: bool = True) -> None:
    import requests  # requests is optional; prefer it if available

    with requests.get(url, headers=headers, timeout=timeout, stream=stream) as r:
        r.raise_for_status()
        total = 0
        tmp = out_path + ".part"
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)
        if total == 0:
            raise RuntimeError("Downloaded file is empty")
        os.replace(tmp, out_path)


def download_with_urllib(url: str, out_path: str, headers: dict, timeout: int = 20) -> None:
    import urllib.request
    import urllib.error

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None)
            if status is not None and status >= 400:
                raise RuntimeError(f"HTTP error: {status}")
            data = resp.read()
            if not data:
                raise RuntimeError("Downloaded file is empty")
            tmp = out_path + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, out_path)
    except urllib.error.HTTPError as e:
        # Raise a clearer error
        raise RuntimeError(f"HTTP Error {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL Error: {e.reason}") from e


def download_pdf(url: str, out_path: str, retries: int = 2, backoff: float = 1.5) -> None:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            # Prefer requests if installed
            try:
                download_with_requests(url, out_path, headers=BROWSER_HEADERS)
            except Exception as rexc:
                # If requests not available or fails, fallback to urllib implementation
                if isinstance(rexc, ModuleNotFoundError):
                    download_with_urllib(url, out_path, headers=BROWSER_HEADERS)
                else:
                    # If requests exists but raises an HTTPError (e.g. 403), re-raise to be handled below
                    raise
            return
        except Exception as e:
            last_exc = e
            if attempt < retries:
                wait = backoff * (2 ** attempt)
                print(f"Attempt {attempt+1} failed: {e!r}. Retrying in {wait:.1f}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise last_exc


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Download NCFC LatestAgriculturalCondAsses.pdf and save with today's date")
    p.add_argument("--to", "-t", dest="to", default=None, help="Target directory (default: ~/Downloads)")
    p.add_argument("--url", dest="url", default=URL_DEFAULT, help="PDF URL (default: NCFC report)")
    p.add_argument("--name", dest="name", default=DEFAULT_NAME, help="Base filename (default: LatestAgriculturalCondAsses)")
    p.add_argument("--retries", dest="retries", type=int, default=2, help="Retries on failure (default 2)")
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
        print(f"Failed to download: {e}", file=sys.stderr)
        return 2

    # Basic verification
    try:
        size = os.path.getsize(out_path)
    except OSError:
        print("Failed to stat downloaded file", file=sys.stderr)
        return 3
    if size == 0:
        print("Downloaded file is zero bytes", file=sys.stderr)
        return 4

    print(f"Success: saved {out_path} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
