#!/usr/bin/env python3
"""
Download LatestAgriculturalCondAsses.pdf from ncfc.gov.in and save to downloads/
"""
import os
import sys
import argparse
import datetime
import time

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except Exception:
    requests = None


def create_session_with_retries(retries=3, backoff_factor=0.5):
    """Create a requests session with retry strategy and proper headers."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=retries,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=backoff_factor
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Add User-Agent header to mimic browser request
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    return session


def download(url, out_dir):
    if requests is None:
        raise RuntimeError("requests is required. Install it with `pip install requests` or let the workflow install dependencies.")
    os.makedirs(out_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    filename = f"LatestAgriculturalCondAsses-{today}.pdf"
    path = os.path.join(out_dir, filename)

    # Create session with retry logic and proper headers
    session = create_session_with_retries()
    
    try:
        # stream the response to avoid loading the whole file into memory
        with session.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return path
    finally:
        session.close()


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
