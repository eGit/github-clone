#!/usr/bin/env python
# -*- encoding: utf-8
"""
GitHub clone (git.io/ghclone)

Usage:
  ghclone <url> [-t | --token=<token>]
  ghclone (-h | --help)
  ghclone (-v | --version)

Examples:
  ghclone https://github.com/HR/Crypter/tree/master/app
  ghclone https://github.com/HR/Crypter/tree/dev/app
  ghclone https://github.com/HR/Crypter/tree/v3.1.0/build
  ghclone https://github.com/HR/Crypter/tree/cbee54dd720bb8aaa3a2111fcec667ca5f700510/build
  ghclone https://github.com/HR/Picturesque/tree/master/app/src -t li50d67757gm20556d53f08126215725a698560b

Options:
  -h --help           Show this screen.
  -v --version        Show version.
  -t --token=<token>  Set a GitHub OAuth token (see https://developer.github.com/v3/#rate-limiting).

(C) 2019 Habib Rehman (git.io/HR)
"""
import requests
import re
import os
import errno
from sys import exit
from docopt import docopt

__version__ = '1.0.0'
GH_API_BASE_URL = 'https://api.github.com'
GH_REPO_CONTENTS_ENDPOINT = GH_API_BASE_URL + '/repos/{}/{}/contents'
BASE_NORMALIZE_REGEX = re.compile(r'.*github\.com\/')

req = requests.Session()
req.headers.update({'User-Agent': 'git.io/ghclone '+__version__})

def exit_with_m(m='An error occured'):
    print(m)
    exit(1)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as err:  # Python >2.5
        if err.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def clone_file(download_url, file_path):
    """
    Clones the file at the download_url to the file_path
    """
    r = req.get(download_url, stream=True)
    try:
        r.raise_for_status()
    except Exception as e:
        exit_with_m('Failed cloning ' + download_url, e)

    with open(file_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

def clone(base_url, path=None, ref=None):
    """
    Recursively clones the path
    """
    req_url = base_url if not path else os.path.join(base_url, path)
    # Get path metadata
    r = req.get(req_url) if not ref else req.get(req_url, params={'ref': ref})
    try:
        r.raise_for_status()
    except Exception as e:
        exit_with_m('Failed fetching metadata for ' + path, e)
    repo_data = r.json()

    # Create path locally
    mkdir_p(path)

    if isinstance(repo_data, list):
        # Recursively clone content
        for item in repo_data:
            if item['type'] == 'dir':
                # Fetch dir recursively
                clone(base_url, item['path'], ref)
            else:
                # Fetch the file
                clone_file(item['download_url'], item['path'])
                print('Cloned', item['path'])


###
# Main
###
def main():
    arguments = docopt(__doc__)
    if arguments['--version']:
        print(__version__)
        exit(0)

    # Get params
    gh_url = arguments['<url>']
    token = arguments['--token']
    if token:
        req.headers.update({'Authorization': 'token '+token[0]})
    # Normalize & parse input
    normal_gh_url = re.sub(BASE_NORMALIZE_REGEX, '', gh_url).replace('/tree', '')
    gh_url_comps = normal_gh_url.split('/')
    user, repo = gh_url_comps[:2]
    ref = gh_url_comps[2]
    path = os.path.join(*gh_url_comps[3:])
    api_req_url = GH_REPO_CONTENTS_ENDPOINT.format(user, repo)
    print("Cloning into '%s'..." % path)
    clone(api_req_url, path, ref)
    print("done.")

if __name__ == '__main__':
    main()
