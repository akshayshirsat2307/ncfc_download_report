#!/usr/bin/env python3
"""
Download LatestAgriculturalCondAsses.pdf from ncfc.gov.in and save to downloads/
"""
import os
import sys
import argparse
import datetime

try:
    import requests
except Exception:
    requests = None


def download(url, out_dir):
    if requests is None:
        raise RuntimeError("requests is required. Install it with `pip install requests` or let the workflow install dependencies.")
    os.makedirs(out_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    filename = f"LatestAgriculturalCondAsses-{today}.pdf"
    path = os.path.join(out_dir, filename)

    # stream the response to avoid loading the whole file into memory
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return path


def main():
    parser = argparse.ArgumentParser(description="Download LatestAgriculturalCondAsses.pdf and save it to a folder")
    parser.add_argument("--url", default="https://www.ncfc.gov.in/downloads/LatestAgriculturalCondAsses.pdf", help="PDF URL to download")
    parser.add_argument("--out", default="downloads", help="Output directory")
    args = parser.parse_args()

    try:
        path = download(args.url, args.out)
        print(f"Saved: {path}")
    except Exception as e:
        print("Download failed:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
