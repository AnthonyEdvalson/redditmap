"""top 40 accounts on:
Twitter
Reddit
Youtube
Facebook

Look at last 1000 words posted from each, find average sentiment"""

import praw
import json

with open("reddit.txt") as f:
    users = f.read().split("\n")

reddit = praw.Reddit(
    client_id="MPLgiAm9vLBTYA",
    client_secret="vcCg0YryVXht5B3CaqGs1tZkDOKGHQ",
    password="Z1gp.hzjilk16b1k",
    username="Dysprosia1",
    user_agent="python:sentiment:v1 (by u/dysprosia1)"
)

with open("reddit_cacheX.json", "r+") as f:
    data = json.loads(f.read())


def load_comment(c):
    if (c.author_flair_text and "mod" in c.author_flair_text) or c.distinguished or c.stickied:
        return None

    return c.body


for user in users:
    if user in data:
        continue

    if len(data.keys()) >= 40:
        print("DONE")
        break

    try:
        comments = list(reddit.redditor(user).comments.top("all", limit=100))
    except:
        print(user + " FAIL")
        continue

    filtered = []
    for comment in comments:
        text = load_comment(comment)
        if text:
            filtered.append(text)

    if len(filtered) < 50:
        print(user + " NO DATA")
        continue

    data[user] = filtered


    with open("reddit_cacheX.json", "w") as f:
        f.write(json.dumps(data))
    print(user)
