#!/usr/bin/env python3
"""上传论文 zip 到 GitHub Releases"""
import json, os, http.client, urllib.parse

TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    print("请先设置: set GH_TOKEN=你的github_token")
    sys.exit(1)
REPO = "SDFGAEV/math_modeling-agent"
RELEASES_DIR = "E:/math_modeling/releases_new"

ENGLISH_NAMES = {
    "papers-仿真综合类.zip": "papers-simulation.zip",
    "papers-优化类.zip": "papers-optimization.zip",
    "papers-图论网络类.zip": "papers-graph-network.zip",
    "papers-统计类.zip": "papers-statistics.zip",
    "papers-评价类.zip": "papers-evaluation.zip",
    "papers-预测类.zip": "papers-prediction.zip",
}

def gh_api(method, path, body=None):
    """通用 GitHub API 调用"""
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "upload_releases/1.0",
    }
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    if resp.status >= 400:
        raise Exception(f"HTTP {resp.status}: {data.decode()[:500]}")
    return json.loads(data) if data else {}

# 1. 获取 release upload URL
release = gh_api("GET", f"/repos/{REPO}/releases/tags/v1.0")
upload_url = release["upload_url"].split("{")[0]
print(f"Release: {release['html_url']}")

# 2. 上传每个文件
parsed = urllib.parse.urlparse(upload_url)
host = parsed.hostname

for fname, ename in sorted(ENGLISH_NAMES.items()):
    fpath = os.path.join(RELEASES_DIR, fname)
    if not os.path.exists(fpath):
        print(f"SKIP {fname}: not found")
        continue

    size_mb = os.path.getsize(fpath) // (1024 * 1024)
    print(f"Uploading {ename} ({size_mb}MB)...", end=" ", flush=True)

    with open(fpath, "rb") as f:
        body = f.read()

    path = f"{parsed.path}?name={urllib.parse.quote(ename)}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/zip",
        "User-Agent": "upload_releases/1.0",
    }
    conn = http.client.HTTPSConnection(host)
    conn.request("POST", path, body=body, headers=headers)
    resp = conn.getresponse()
    result = resp.read()
    conn.close()

    if resp.status == 201:
        asset = json.loads(result)
        print(f"OK ({asset['browser_download_url']})")
    else:
        print(f"FAILED: HTTP {resp.status} {result.decode()[:200]}")

print(f"\nDone! https://github.com/SDFGAEV/math_modeling-agent/releases/tag/v1.0")
