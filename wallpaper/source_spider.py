import requests


def get_source(url='http://images.acgmonster.com/shine/wallpapers/eaaf6f4acc4563de47a6480bd4bb48cb.mp4'):
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.content
    return None
