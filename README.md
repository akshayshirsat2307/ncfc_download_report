# ncfc_download_report

This repository contains a small script to automatically download the NCFC (National Centre For Forecasting & Climate?) daily PDF report.

Report URL

- https://www.ncfc.gov.in/downloads/LatestAgriculturalCondAsses.pdf

Files added

- scripts/download_report.py — Python script to download the PDF and save it to ~/Downloads (or a custom path).

Usage

1. Run locally:

   ```bash
   python3 scripts/download_report.py
   # or specify a target directory
   python3 scripts/download_report.py --to /path/to/dir
   ```

2. Schedule daily with cron (example runs at 06:00 daily):

   ```cron
   0 6 * * * /usr/bin/python3 /full/path/to/repo/scripts/download_report.py >> /full/path/to/repo/logs/download_report.log 2>&1
   ```

Notes

- If the server blocks requests from non-browser User-Agents, edit the User-Agent header in the script.
- The script will name the file LatestAgriculturalCondAsses_YYYY-MM-DD.pdf.
- For improvements, consider adding logging, retention policy, or a GitHub Action to store artifacts.
