import sqlite3
import praw
import OAuth2Util
import requests
import json


user_agent = "r6stats by /u/jake0oo0 v0.1"

cfile = open('config.json')
config = json.load(cfile)
botuser = config['username']
subreddits = '+'.join(config['subreddits'])

reply = ""


def checkComments(subreddit):
    sub = r.get_subreddit(subreddit)
    comments = sub.get_comments(limit=250)

    for comment in comments:
        guid = comment.id
        # print(guid)
        if comment.author.name == botuser:
            print("Ignorning own comment")
            continue

        cur.execute('SELECT * FROM items WHERE id=?', [guid])
        if cur.fetchone():
            print('Comment already checked')
            continue

        body = comment.body
        if "u/{}".format(botuser.lower()) not in body.lower():
            print("Not tagged in the comment")
            continue

        print("Extracting players!")

        players = extractPlayers(body)

        if len(players) == 0:
            continue

        global reply
        reply = createMessage(players)

        # print(reply)
        try:
            comment.reply(reply)
            cur.execute('INSERT INTO items VALUES(?)', [guid])

            sql.commit()

        except praw.errors.Forbidden:
            print("The bot has been banned from {}".format(subreddit))
            continue
        except praw.errors.RateLimitExceeded:
            print("Rate limit exceeded, skipping comment for now")
            continue

keys = ['/u/{}'.format(botuser.lower()), 'u/{}'.format(botuser.lower())]


def extractPlayers(body):
    body = body.lower()
    tokens = body.split()

    b = [item for item in range(len(tokens)) if tokens[item] in keys]
    players = []
    for index in b:
        # check that there is even room for username and platform
        if len(tokens) < (index + 3):
            continue
        # username is first arg
        username = tokens[index + 1]
        # platform is second arg
        platform = tokens[index + 2]
        print("Username: {} Platform: {}".format(username, platform))
        p = {"username": username, "platform": platform}
        players.append(p)
    return players


def createMessage(players):
    message = ""
    for idx, data in enumerate(players):
        username = data['username']
        platform = data['platform']
        gamemode = "ranked"

        player = requestPlayer(username, platform)
        if idx > 0:
            message += "\n\n"
        if player is None:
            message += ("{} ({}): Player not found").format(username, platform)
        else:
            stats = player["player"]["stats"]
            actual = player["player"]["username"]
            ranked = stats["ranked"]
            casual = stats["casual"]
            message += "{} *({})*:\n\n".format(actual, getPlatform(platform))
            message += "Stat|Casual|Ranked\n"
            message += ":--|:--|:--\n"
            message += "Kills|{}|{}\n".format(casual["kills"], ranked["kills"])
            message += "Deaths|{}|{}\n".format(casual["deaths"], ranked["deaths"])
            message += "K/D|{}|{}\n".format(casual["kd"], ranked["kd"])
            message += "Wins|{}|{}\n".format(casual["wins"], ranked["wins"])
            message += "Losses|{}|{}\n".format(casual["losses"], ranked["losses"])
            message += "W/L|{}|{}\n".format(casual["wlr"], ranked["wlr"])
    message += "^(*Hello, I am a bot!*)\n\n"
    message += "You can summon me with ```/u/{} <username> <platform>```. Data via [R6Stats](https://r6stats.com).\n\n".format(config['username'])
    message += "[[Info](https://reddit.com/r/R6Stats)] [[Source](https://github.com/R6Stats/reddit-bot)]"
    return message


def getPlatform(plat):
    if plat == "xone":
        return "Xbox One"
    elif plat == "ps4":
        return "PS4"
    elif plat == "uplay":
        return "Uplay"


def requestPlayer(username, platform):
    r = requests.get('https://api.r6stats.com/api/v1/players/{}?platform={}'.format(username, platform))
    json = r.json()

    if r.status_code == 404:
        return None
    else:
        return json

if __name__ == '__main__':
    r = praw.Reddit(user_agent)
    o = OAuth2Util.OAuth2Util(r)
    o.refresh(force=True)
    print('Successful log in')

    sql = sqlite3.connect('sql.db')
    cur = sql.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS items(id TEXT)')

    checkComments(subreddits)
