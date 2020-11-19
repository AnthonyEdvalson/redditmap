import math

from praw.models.listing.mixins.redditor import SubListing
from scipy.stats import beta
import praw
import sqlite3
import logging
import time
from urllib.parse import urljoin

"""
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
for logger_name in ("praw", "prawcore"):
   logger = logging.getLogger(logger_name)
   logger.setLevel(logging.DEBUG)
   logger.addHandler(handler) """

MIN_PER_SUB = 4


sub_lookup = {}
with open('lookup.txt') as f:
    for line in f.read().split("\n"):
        if not line:
            continue

        name, count = line.split("\t")
        sub_lookup[name] = int(count.replace(",", ""))


reddit = praw.Reddit(
    client_id="MPLgiAm9vLBTYA",
    client_secret="vcCg0YryVXht5B3CaqGs1tZkDOKGHQ",
    password="xxx",
    username="xxx",
    user_agent="python:sentiment:v1 (by u/dysprosia1)"
)

searched_subs = set()
searched_users = set()

sub_sightings = {'funny': 5}

db = sqlite3.connect('links.db')
# create table user (name varchar(25) primary key, mod integer, gold integer, karma integer);
# create table sub (name varchar(25) primary key, nsfw integer, subscribers Integer);
# create table link (user_name varchar(25), sub_name varcher(25), power integer, PRIMARY KEY (user_name, sub_name));
# create table lead (type integer, name varchar(25), PRIMARY KEY (type, name));

completed_work = 1
total_work = 1


class Transact:
    def __init__(self, sql):
        self.c = sql.cursor()

    def __enter__(self):
        self.c.execute("BEGIN")
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.c.execute("rollback")
        else:
            self.c.execute("commit")


with Transact(db) as c:
    c.execute("DELETE FROM lead")
    c.execute("DELETE FROM user")
    c.execute("DELETE FROM link")
    c.execute("DELETE FROM sub")


def explore_redditor(name):
    global total_work, completed_work, sub_sightings
    if name in searched_users:
        return set()

    user = reddit.redditor(name)
    subs = {}

    # posts = user.submissions.new(limit=8)  # comments / 12

    print("Exploring u/" + name)

    comment_score = 1
    # post_score = 12  # site-wide, Reddit has 12 comments per post
    try:
        comments = user.comments.new(limit=100)
        for comment in comments:
            id = comment.subreddit_name_prefixed[2:]

            if id in subs:
                subs[id] += comment_score
            else:
                subs[id] = comment_score
    except:
        print("FAILED TO GET COMMENTS")
        return set()

    """for post in posts:
        id = post.subreddit_name_prefixed[2:]

        if id in subs:
            subs[id] += post_score
        else:
            subs[id] = post_score"""

    with Transact(db) as c:
        # user data is zeroed out for the moment to speed up the search
        c.execute("INSERT OR REPLACE INTO user VALUES (?,?,?,?)", (name, 0, 0, 0))  # user.is_mod, user.is_gold, user.comment_karma + user.link_karma))
        for sub, power in subs.items():
            c.execute("INSERT OR REPLACE INTO link VALUES (?,?,?)", (name, sub, power))

    searched_users.add(name)

    for sub in subs.keys():
        if sub not in sub_sightings:
            sub_sightings[sub] = 1
        else:
            sub_sightings[sub] += 1

    return set(subs.keys())


def explore_sub(name, target_sat):
    global total_work, completed_work

    # Ignore if already searched
    if name in searched_subs:
        return set()

    # Ignore if stats are bad
    # thresh is number of users needed for this sub to have associated users
    thresh = MIN_PER_SUB / target_sat
    if name in sub_lookup:
        valid_chance = 1 if sub_lookup[name] > thresh else 0
    else:
        min_p = thresh / 70000000  # 70M is total reddit population
        sightings = sub_sightings[name]
        # Find the chance that this sub has enough people
        valid_chance = 1 - beta.cdf(min_p, 1 + sightings, 1 + max(0, len(searched_users) - sightings))

    # Need to be 90% sure
    if valid_chance < 0.9:
        return set()

    print("Exploring ({:.2f}) r/{}".format(valid_chance, name), end="")

    try:
        sub = reddit.subreddit(name)
        subscribers = sub.subscribers
        portion = math.floor(subscribers * target_sat)
    except:
        print("\nFailed to load r/" + name)
        return set()

    print(" and " + str(portion) + " users")

    if portion > 1024:
        print("CUTOFF")

    users = set()
    if portion > MIN_PER_SUB:
        for post in sub.new(limit=portion):
            users.add(str(post.author))

        with Transact(db) as c:
            c.execute("INSERT OR REPLACE INTO sub VALUES (?,?,?)", (sub.display_name, sub.over18, subscribers))

    searched_subs.add(name)

    return users


def get_all_saturations():
    sub_saturations = {}

    with Transact(db) as c:
        c.execute("SELECT * FROM sub")
        subs = c.fetchall()

    for sub in subs:
        with Transact(db) as c:
            c.execute("SELECT COUNT(*) FROM link WHERE sub_name = ?", (sub[0], ))
            count = c.fetchone()[0]

        sub_saturations[sub[0]] = count / sub[2]

    return sub_saturations


def log(complete, total, start):
    now = time.time()
    dur = now - start
    proj = dur * (total / complete) - dur
    sec = int(proj) % 60
    min = int(proj / 60) % 60
    hour = int(proj / 60 / 60)
    print("{:.2f}% ({}/{}) {}:{}:{}".format(complete / total * 100, complete, total, hour, min, sec))


def main_loop():
    global total_work, completed_work

    users = set()
    subs = {"funny"}

    while len(subs) > 0:
        total_work += len(subs)
        for sub in subs:
            users = set.union(users, explore_sub(sub, target_saturation))
            completed_work += 1
            new_total = total_work + len(users)
            log(completed_work, new_total, start)
        subs = set()

        total_work += len(users)
        for user in users:
            subs = set.union(subs, explore_redditor(user))
            completed_work += 1
            new_total = total_work + len(subs)
            log(completed_work, new_total, start)
        users = set()


target_saturation = (1 / 90000) * MIN_PER_SUB
print("Min sub size: " + str(int(round(MIN_PER_SUB / target_saturation))))
start = time.time()
main_loop()
#explore_sub("funny", target_saturation)
main_loop()
end = time.time()

sub_count = len(searched_subs)
user_count = len(searched_users)

print("Collection took {:.2f} minutes to get {} subs and {} users".format((end - start) / 60, sub_count, user_count))
# 1 / 6M ->  0.13 min
# 1 / 5M ->  0.27 min (75)
# 1 / 4M ->  0.48 min (139)
# 1 / 3M -> 25.16 min (6563), only 1121 were useful
#
# -------------------------------------------------
#
# 1 / 3M ->  5.58 min (3276), 109 subs
# 1 / 2M ->  8.15 min (6260), 118 subs
# 1 / 500K -> 50.01 min (42348), 477 subs

# With sub lookup table:
# 1 / 500K -> 74.67 min (59890), 867 subs
# 2x 1 / 100K -> Collection took 303.98 minutes to get 1742 subs and 15578 users



"""
Subreddit size follows zipf's law, with the exception of the A-list subreddits, which are promoted more often and tend to
have many more subscribers. The equation for sub size is (4.1 * 10^8) / x, where x is the rank of the subreddit.

We need a solid filter for sub size, specifically we need to be able to anticipate the size of a subreddit based on the
number of times it has been seen in our sampling of users. I'm not aware of any techniques for this particular problem
so it time to make some math.

CDF of 1/x is ln(n) / ln(N) or log_N(n), where N is the maximum value. In practice this should be adjusted to match the data.

After searching u users and finding n edges to a subreddit, what is the chance that it has at least x subscribers?

Easiest way to do this is to find a cutoff (2 users, 4 users, etc) in advance based on the parameters. We'll call this function
c(u, x). Of course this function will need to have some confidence value baked into it. 85% confidence is good enough for this purpose.

The Beta distribution will come in handy. The exact details of how it's used is pretty obscure, but the important part is
that is can be used to estimate the underlying probability based on a series of outcomes. In this case the underlying probability
is the chance that a user is subscribed to a subreddit. This probability multiplied by the number of active users gives the
number of subscribers. So estimating the probability estimates subscriber counts. The best part is it updates nicely with new data.
B(1 + # of users subbed, 1 + # of users not subbed, p) is the PDF of p being the actual probability.

Take the integral from the threshold percentage upwards, and that's the chance that the sub has enough subs. If the chance
is above a threshold, then it is reasonable to investigate further.

"""
