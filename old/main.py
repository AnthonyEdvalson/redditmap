"""
sentiment by subreddit.
"""

import praw
import json

with open("subs.txt") as f:
    subs = f.read().split("\n")

reddit = praw.Reddit(
    client_id="MPLgiAm9vLBTYA",
    client_secret="vcCg0YryVXht5B3CaqGs1tZkDOKGHQ",
    password="Z1gp.hzjilk16b1k",
    username="Dysprosia1",
    user_agent="python:sentiment:v1 (by u/dysprosia1)"
)

with open("reddit_cache.json", "r+") as f:
    data = json.loads(f.read())


for sub in subs:
    if sub in data:
        continue

    if len(data.keys()) >= 60:
        print("DONE")
        break

    best = list(reddit.subreddit(sub).top("all", limit=100))

    filtered = []
    q = 0
    for post in best:
        d = {
            "id": post.id,
            "is_oc": post.is_original_content,
            "title": post.title,
            "comment_count": post.num_comments,
            "score": post.score,
            "text": post.selftext
        }

        q0 = len(d["title"]) + len(d["text"])
        if q0 < 45:
            continue

        q += q0
        filtered.append(d)

    if len(filtered) < 50:
        print(sub + " NO DATA")
        continue

    data[sub] = filtered

    with open("reddit_cache.json", "w") as f:
        f.write(json.dumps(data))
    print(sub)
