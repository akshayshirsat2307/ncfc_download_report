#!/usr/bin/env python3
"""
Downloader for NCFC LatestAgriculturalCondAsses.pdf.

Behavior:
- When a relative --to is provided (for example --to downloads), the path is resolved
  relative to the script file location (os.path.dirname(__file__)), so the downloads
  folder will be created next to this script.
- If --to is absolute, it is used as given.
- If --to is omitted:
    - In GitHub Actions: defaults to $GITHUB_WORKSPACE/downloads (repo checkout dir)
    - Locally: defaults to ~/Downloads

Usage:
  python ncfc_download_report_code.py
  python ncfc_download_report_code.py --to downloads
  python ncfc_download_report_code.py --to /absolute/path
"""
from __future__ import annotations
import argparse
import datetime
import os
import sys
import time

URL_DEFAULT = "https://www.ncfc.gov.in/downloads/LatestAgriculturalCondAsses.pdf"
DEFAULT_NAME = "LatestAgriculturalCondAsses"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/octet-stream,application/*;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.ncfc.gov.in/",
}


def make_filename(base_name: str, date: datetime.date) -> str:
    return f"{base_name}_{date.isoformat()}.pdf"


def save_debug_html(out_dir: str, name: str, body: bytes) -> None:
    path = os.path.join(out_dir, f"{name}.debug.html")
    try:
        with open(path, "wb") as f:
            f.write(body)
        print(f"Saved debug HTML: {path}")
    except Exception as e:
        print(f"Failed to save debug HTML: {e}", file=sys.stderr)


def download_with_requests(url: str, out_path: str, headers: dict, timeout: int = 20) -> None:
    import requests

    # HEAD for diagnostics
    try:
        head = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        print(f"HEAD status: {head.status_code}")
        for k, v in head.headers.items():
            print(f"HEAD header: {k}: {v}")
    except Exception as e:
        print(f"HEAD request failed: {e}", file=sys.stderr)

    with requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True) as r:
        print(f"GET status: {r.status_code}")
        for k, v in r.headers.items():
            print(f"GET header: {k}: {v}")
        if r.status_code >= 400:
            body = r.content or (r.text.encode("utf-8", errors="replace") if hasattr(r, "text") else b"")
            save_debug_html(os.path.dirname(out_path) or ".", "download_error", body)
            r.raise_for_status()
        tmp = out_path + ".part"
        total = 0
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
            print(f"urllib GET status: {status}")
            if status is not None and status >= 400:
                body = resp.read() or b""
                save_debug_html(os.path.dirname(out_path) or ".", "download_error", body)
                raise RuntimeError(f"HTTP error: {status}")
            data = resp.read()
            if not data:
                raise RuntimeError("Downloaded file is empty")
            tmp = out_path + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, out_path)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP Error {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL Error: {e.reason}") from e


def download_pdf(url: str, out_path: str, retries: int = 2, backoff: float = 1.5) -> None:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            try:
                download_with_requests(url, out_path, BROWSER_HEADERS)
            except ModuleNotFoundError:
                download_with_urllib(url, out_path, BROWSER_HEADERS)
            return
        except Exception as e:
            last_exc = e
            if attempt < retries:
                wait = backoff * (2 ** attempt)
                print(f"Attempt {attempt+1} failed: {e!r}. Retrying in {wait:.1f}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise last_exc


def resolve_target_dir(requested: str | None) -> str:
    """
    Resolve the requested target directory to an absolute path.

    Rules:
    - If requested is absolute: use it as-is.
    - If requested is relative: resolve relative to the script's directory (dir of this file).
    - If requested is None:
        - If running in Actions and GITHUB_WORKSPACE is set -> use $GITHUB_WORKSPACE/downloads
        - Else -> ~/Downloads
    """
    if requested is not None and os.path.isabs(requested):
        return requested

    script_dir = os.path.dirname(os.path.abspath(__file__))

    if requested is None:
        if os.environ.get("GITHUB_ACTIONS", "false").lower() == "true":
            github_workspace = os.environ.get("GITHUB_WORKSPACE")
            if github_workspace:
                # prefer the checked-out workspace downloads
                return os.path.abspath(os.path.join(github_workspace, "downloads"))
        return os.path.abspath(os.path.expanduser("~/Downloads"))

    # requested is relative -> place under script directory
    return os.path.abspath(os.path.join(script_dir, requested))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Download NCFC LatestAgriculturalCondAsses.pdf and save with today's date")
    p.add_argument("--to", "-t", dest="to", default=None, help="Target directory (absolute or relative to script location).")
    p.add_argument("--url", dest="url", default=URL_DEFAULT, help="PDF URL (default: NCFC report)")
    p.add_argument("--name", dest="name", default=DEFAULT_NAME, help="Base filename (default: LatestAgriculturalCondAsses)")
    p.add_argument("--retries", dest="retries", type=int, default=2, help="Retries on failure (default 2)")
    args = p.parse_args(argv)

    target_dir = resolve_target_dir(args.to)
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
