
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
