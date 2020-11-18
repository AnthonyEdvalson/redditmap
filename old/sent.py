import json


def csv(data):
    text = ""
    for k, vs in data.items():
        s = ""
        for v in vs:
            s += (v["title"] + ": " + v["text"]).replace("\"", "").replace(",", "").replace("\n", "")[:100] + " | "

        text += k + "," + s + "\n"

    return text


with open("reddit_cache.json", "r") as f:
    d = json.loads(f.read())
    s = csv(d)

    print(s)

with open("csv.csv", "w+") as f:
    f.write(s)
