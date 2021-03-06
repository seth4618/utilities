#!/usr/bin/env python

# will unsubscribe from notifications from all repos in an
# organization.  requires a "personal access token" from github.  Goto
# settings, developer settings, personal access token to get one if
# you have env var set GITUNSUB to a path, it will keep track of last
# page fetched from an org and start


import requests
import argparse
import re
import json
from requests.auth import HTTPBasicAuth
import os
import errno
from pprint import pprint

import sys
if sys.version_info >= (3, 6):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


def die(msg):
    print(msg)
    exit(-1)


################################################################
# setup arguments
parser = argparse.ArgumentParser(description='get all repos and ignore message for each for an org',
                                 epilog='''

                                 preforms actions on behalf of user defined in environment variable GITHUB_USER.
                                 It uses the the token defined by GITHUB_PERSONAL_ACCESS_TOKEN.
                                 If GITHUB_UNSUB is defined to a file path, will store last page acted on in the file
                                 and by default will start searching next time from this page.  On ubuntu GITHUB_UNSUB=~/.config/githubunsub/lastpage.json would be a reasonable definition.''')
parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase output verbosity")
parser.add_argument("-o", "--org", default="cmu15213f21", help="org to work on")
parser.add_argument("-s", "--start", type=int, default=0, help="page to start at")
parser.add_argument("-u", "--user", default="", help="github user (overrides environment)")
parser.add_argument("-t", "--token", default="", help="github token (overrides environment")
flags = parser.parse_args()

verbose = flags.verbosity
org = flags.org
startPage = flags.start
user = flags.user
token = flags.token

# deal with user/token from environment
if len(user) == 0:
    user = os.getenv("GITHUB_USER")
    if user is None:
        die("No user specified, please set GITHUB_USER or use -u")
if len(token) == 0:
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if token is None:
        die("No token specified, please set GITHUB_PERSONAL_ACCESS_TOKEN or use -t")

# see if we are tracking orgs, if so then use last page fetched as default start point
tracking = os.getenv("GITHUB_UNSUB")
unsubTracking = {}
if tracking is not None:
    if os.path.exists(tracking):
        unsubTracking = json.load(open(tracking, "r"))
    if (startPage == 0) and (org in unsubTracking):
        startPage = unsubTracking[org]
# we didn't set start on command line or find info in tracking file
if startPage == 0:
    startPage = 1


# exception raised if we get a 404 from github api
class NotFoundError(Exception):
    pass


# execute get with authorization, return json object
def authget(path, query):
    r = requests.get("https://api.github.com{}".format(path),
                     headers={"Accept": "application/vnd.github.v3+json",
                              "User-Agent": "seths unsub"},
                     auth=HTTPBasicAuth(user, token),
                     params=query)
    if r.status_code == 404:
        raise NotFoundError()
    elif r.status_code != 200:
        raise ValueError("Bad status {} from Get {}".format(r.status_code, path))
    return r.json()


# execute PUT with authorization, return json object
def authput(path, obj):
    r = requests.put("https://api.github.com{}".format(path),
                     headers={"Accept": "application/vnd.github.v3+json",
                              "User-Agent": "seths unsub"},
                     auth=HTTPBasicAuth(user, token),
                     data=json.dumps(obj))
    if r.status_code == 404:
        raise NotFoundError()
    elif r.status_code != 200:
        raise ValueError("Bad status {} from Get {}".format(r.status_code, path))
    return r.json()


page = startPage
numrepo = 0
numignored = 0
setignored = 0
while True:
    print("Getting page {} on {}".format(page, org))
    result = authget("/orgs/{}/repos".format(org), {"per_page": "50", "page": page})
    if len(result) == 0:
        break
    for repo in result:
        numrepo += 1
        # print("sub: {}".format(repo["subscription_url"]))
        try:
            subpath = urlparse(repo["subscription_url"]).path
            subinfo = authget(subpath, None)
            if not subinfo['ignored']:
                m = re.search("/([^/]+)/[^/]+$", subpath)
                if m is None:
                    raise ValueError("Badly formed path to repo: {}".format(subpath))
                reponame = m.group(1)
                newinfo = authput(subpath, {'ignored': True})
                if not newinfo['ignored']:
                    print("failed to ignore {}".format(reponame))
                    pprint(newinfo)
                else:
                    setignored += 1
                    print("Ignored: {}".format(reponame))
            else:
                numignored += 1
        except NotFoundError:
            numignored += 1     # actually, not subscribed.  Same thing for now
    page += 1

print("Repos: {}, already ignored: {}, set to ignored: {}".format(numrepo, numignored, setignored))

# if we are tracking, save info
if tracking is not None:
    unsubTracking[org] = page - 1
    try:
        os.makedirs(os.path.dirname(tracking))  # make sure directory exists for file
    except OSError as e:
        if e.errno != errno.EEXIST:
            print("Failed to create the tracking directory:{}".format(tracking))
            raise e
    with open(tracking, "w") as f:
        f.write(json.dumps(unsubTracking))
