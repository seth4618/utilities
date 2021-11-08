This script uses the github API to ignore all notifications for all
the repos in a particular organization.

It requires a requires a [personal access
token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
from github.  You can get one by going to settings, developer
settings, personal access token, then follow directions.

Usage:

./unsuborg.py -o <org> -s <startpage> -u <user> -t <token>

- <org> is the organization with repositories you want to ignore
- <startpage> is the page number.  defaults to 1.  If you have lots of repositories and know that the first n have already been ignored, you can set <startpage> to n.  Each page lists 50 repos
- <user> is the user doing the operation
- <token> is your personal access token

You can set environment variables so you don't have to specifiy -u and -t:

- GITHUB_USER=<github-user-id>
- GITHUB_PERSONAL_ACCESS_TOKEN=<personal-access-token>
