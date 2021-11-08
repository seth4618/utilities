#!/usr/bin/env python

import requests
import argparse
import re
import json
from requests.auth import HTTPBasicAuth
from pprint import pprint

import sys
if sys.version_info >= (3, 6):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


################################################################
# setup arguments
parser = argparse.ArgumentParser(description='get all repos and subsription status for an org')
parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase output verbosity")
parser.add_argument("-o", "--org", default="cmu15213f21", help="org to work on")
parser.add_argument("-s", "--start", type=int, default=1, help="page to start at")
flags = parser.parse_args()

verbose = flags.verbosity
org = flags.org
startPage = flags.start

user = "seth4618"
token = "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"


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
    print("Getting page {}".format(page))
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
                m = re.search("/([^/]+)$", subpath)
                if m is None:
                    raise ValueError("Badly formed path to repo: {}".format(subpath))
                reponame = m.group(1)
                newinfo = authput(subpath, {'ignored': True})
                if not newinfo['']:
                    print("failed to ignore {}".format(reponame))
                else:
                    setignored += 1
                    print("Ignored: {}".format(reponame))
            else:
                numignored += 1
        except NotFoundError:
            numignored += 1     # actually, not subscribed.  Same thing for now
    page += 1

print("Repos: {}, already ignored: {}, set to ignored: {}".format(numrepo, numignored, setignored))
