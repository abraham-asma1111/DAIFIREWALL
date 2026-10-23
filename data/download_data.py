import requests

url = "https://cicresearch.ca/CICDataset/CIC-IDS-2017/download.php?file=CIC-IDS-2017%2FCSVs%2FMachineLearningCSV.zip"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://unb.ca"
}

print("Starting download stream...")
with requests.get(url, headers=headers, stream=True) as r:
    r.raise_for_status()
    with open("MachineLearningCSV.zip", "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
print("Download Complete!")
