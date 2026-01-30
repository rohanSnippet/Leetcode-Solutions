import requests
import os
import time
import subprocess

LEETCODE_SESSION = os.getenv("LEETCODE_SESSION")
CSRF_TOKEN = os.getenv("CSRF_TOKEN")

HEADERS = {
    "cookie": f"LEETCODE_SESSION={LEETCODE_SESSION}; csrftoken={CSRF_TOKEN}",
    "x-csrftoken": CSRF_TOKEN,
    "content-type": "application/json",
    "referer": "https://leetcode.com"
}

GRAPHQL_URL = "https://leetcode.com/graphql"

def get_last_synced():
    with open("last_synced.txt", "r") as f:
        return int(f.read().strip())

def update_last_synced(sid):
    with open("last_synced.txt", "w") as f:
        f.write(str(sid))

def fetch_latest_submission():
    query = """
    query {
      submissionList(offset: 0, limit: 5) {
        submissions {
          id
          title
          titleSlug
          lang
          statusDisplay
        }
      }
    }
    """
    res = requests.post(GRAPHQL_URL, json={"query": query}, headers=HEADERS)

    print("STATUS CODE:", res.status_code)
    print("RESPONSE:", res.text)

    data = res.json()
    if "data" not in data or data["data"] is None:
        return None

    return data["data"]["submissionList"]["submissions"]


def fetch_code(submission_id):
    query = """
    query submissionDetails($id: Int!) {
      submissionDetails(submissionId: $id) {
        code
        lang
      }
    }
    """
    res = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": {"id": submission_id}},
        headers=HEADERS
    )
    return res.json()["data"]["submissionDetails"]

def save_solution(title_slug, lang, code):
    ext_map = {"java": "java", "python3": "py", "cpp": "cpp"}
    folder = lang.lower()
    ext = ext_map.get(folder, "txt")

    os.makedirs(folder, exist_ok=True)
    path = f"{folder}/{title_slug}.{ext}"

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

    return path

def git_commit(title):
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"LC: {title}"])
    subprocess.run(["git", "push"])

def main():
    last_synced = get_last_synced()
    submissions = fetch_latest_submission()

    for sub in submissions:
        sid = int(sub["id"])
        if sub["statusDisplay"] != "Accepted":
            continue
        if sid <= last_synced:
            continue

        details = fetch_code(sid)
        path = save_solution(sub["titleSlug"], details["lang"], details["code"])
        git_commit(sub["title"])
        update_last_synced(sid)

        print(f"Synced: {path}")
        break

if __name__ == "__main__":
    main()
