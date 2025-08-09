import requests

class SnapTubeApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def extract_video(self, url: str):
        r = requests.post(f"{self.base_url}/extract/video", json={"url": url})
        r.raise_for_status()
        return r.json()
