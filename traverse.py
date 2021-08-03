import math

from scipy.stats import beta
import praw
import sqlite3
import time

# Minimum number of subscribers per subreddit
COUNT_PER_SUB = 25
MIN_SIZE = 60000
CURIOSITY = 0.4

# Percent of reddit to obtain
#target_saturation = (1 / 90000) * MIN_PER_SUB


# Load the lookup table for subscriber counts
sub_lookup = {}
with open('lookup.txt') as f:
    for line in f.read().split("\n"):
        if not line:
            continue

        name, count = line.split("\t")
        sub_lookup[name] = int(count.replace(",", ""))

with open("api.keys") as f:
    client_id = f.readline()[:-1]
    client_secret = f.readline()[:-1]
    username = f.readline()[:-1]
    password = f.readline()[:-1]
    user_agent = f.readline()[:-1]

print(client_id)
# Connect to Reddit with PRAW
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    password=password,
    username=username,
    user_agent=user_agent
)

# Sets for filtering out searched and bad subreddits and users
# Used to prevent getting on the same users or subs twice
searched_subs = set()
searched_users = set()

# Tracks the number of sightings of each subreddit, r/funny start with 5 to kick things off
sub_sightings = {'funny': 5}

# Connect to the database, below are the list of commands used for each table
db = sqlite3.connect('TEST.db')
# create table user (name varchar(25) primary key, mod integer, gold integer, karma integer);
# create table sub (name varchar(25) primary key, nsfw integer, subscribers Integer);
# create table link (user_name varchar(25), sub_name varchar(25), power integer, PRIMARY KEY (user_name, sub_name));
# create table lead (type integer, name varchar(25), PRIMARY KEY (type, name));

# Used to show progress
completed_work = 1
total_work = 1


# Utility for interacting with the database
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


# Start by wiping all data in the database
with Transact(db) as c:
    c.execute("DELETE FROM lead")
    c.execute("DELETE FROM user")
    c.execute("DELETE FROM link")
    c.execute("DELETE FROM sub")


# Explores a single redditor
def explore_redditor(name):
    global total_work, completed_work, sub_sightings
    if name in searched_users:
        return set()

    user = reddit.redditor(name)
    subs = {}

    # posts = user.submissions.new(limit=8)  # comments / 12

    print("Exploring u/" + name)

    # Count number of comments on each subreddit
    try:
        comments = user.comments.new(limit=100)
        for comment in comments:
            id = comment.subreddit_name_prefixed[2:]

            if id in subs:
                subs[id] += 1
            else:
                subs[id] = 1
    except:
        print("FAILED TO GET COMMENTS")
        return set()

    """for post in posts:
        id = post.subreddit_name_prefixed[2:]

        if id in subs:
            subs[id] += post_score
        else:
            subs[id] = post_score"""

    # Record interactions and user data in database
    with Transact(db) as c:
        # user data is zeroed out for the moment to speed up the search
        c.execute("INSERT OR REPLACE INTO user VALUES (?,?,?,?)", (name, 0, 0, 0))  # user.is_mod, user.is_gold, user.comment_karma + user.link_karma))
        for sub, power in subs.items():
            c.execute("INSERT OR REPLACE INTO link VALUES (?,?,?)", (name, sub, power))

    searched_users.add(name)

    # Record subreddit sightings
    for sub in subs.keys():
        if sub not in sub_sightings:
            sub_sightings[sub] = 1
        else:
            sub_sightings[sub] += 1

    return set(subs.keys())


# Get data on a particular subreddit
def explore_sub(name):
    global total_work, completed_work
    print("r/{: <25}".format(name), end="")

    # Ignore if already searched
    if name in searched_subs:
        print(" has already been searched")
        return set()

    # Ignore if stats are bad
    # thresh is number of users needed for this sub to have associated users
    thresh = MIN_SIZE
    if name in sub_lookup:
        valid_chance = 1 if sub_lookup[name] > thresh else 0
    else:
        min_p = thresh / 70000000  # 70M is total reddit population
        sightings = sub_sightings[name]
        # Find the chance that this sub has enough people
        valid_chance = 1 - beta.cdf(min_p, 1 + sightings, 1 + max(0, len(searched_users) - sightings))

    print(" p={: >3}%".format(str(int(valid_chance * 100))), end="")

    if valid_chance < (1 - CURIOSITY):
        print(", skipping")
        return set()

    print(", exploring", end="")

    try:
        sub = reddit.subreddit(name)
        subscribers = sub.subscribers
        portion = COUNT_PER_SUB
    except Exception as e:
        print("\nFailed to load r/" + name)
        print(e)
        return set()

    if portion > 1024:
        print("CUTOFF")

    users = set()
    if subscribers > MIN_SIZE:
        print(" " + str(portion) + " users")

        for post in sub.new(limit=portion):
            users.add(str(post.author))

        with Transact(db) as c:
            c.execute("INSERT OR REPLACE INTO sub VALUES (?,?,?)", (sub.display_name, sub.over18, subscribers))
    else:
        print(" but too small")

    searched_subs.add(name)

    return users


# Records progress and predicted end time
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

    # As long as there is data to gather, search all subreddits, then search all users
    while len(subs) > 0:
        total_work += len(subs)
        for sub in subs:
            users = set.union(users, explore_sub(sub))
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


print("Min sub size: " + str(MIN_SIZE))
start = time.time()
main_loop()
end = time.time()

sub_count = len(searched_subs)
user_count = len(searched_users)
print("Collection took {:.2f} minutes to get {} subs and {} users".format((end - start) / 60, sub_count, user_count))

