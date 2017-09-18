#!/usr/bin/env python3

### Copyright & Terms of Use ###
# Copyright 2017, Luc Gommans
# You may use, modify and redistribute the code, provided that:
#   1) you don't change your own page or URL to avoid this tool (i.e. if you use it, you must allow also it to use your answers),
#   2) the copyright notice and terms remain, and
#   3) you bring Luc a cookie within a week of first use :-).
################################

accepted_terms_of_use = False

verbose = True
slowly = 0.2 # float seconds between requests, or False

base_url = 'https://www.os3.nl'
year = '2017-2018' # URL component

timeout = 15 # Timeout for HTTP requests
retries = 5 # Number of retries for each HTTP request

cacheFolder = 'cache/'
writeCache = True # Whether to save the result of GETs in cacheFolder
useCache = False # Whether to use those cached files


import sys, os, time, requests
from hashlib import md5
get = requests.get

if len(sys.argv) < 4:
    print('Usage: {} <course> <lab> <question>'.format(sys.argv[0]))
    print('Outputs html to stdout.')
    print('Example: {} cia 2 7 > cia-2-7.html'.format(sys.argv[0]))
    print('It will read from ./cookie.txt which should contain something like:')
    print('DokuWiki=abc89ai4basdifuasdfabcabca; XY1234abfasdfb8a9bifudasudf9iasdf9=ba87BuiSuniufjsioJoifjsadufiaojsdfoijoijsdfioajsidofjoiajs%2Fwhatevertrololol')
    print('')
    print('You can obtain this from the developer console in Firefox: open the dev console (F12) and go to the network tab, load a wiki page while logged in, '
        + 'click on the page request in the console, and grab the value of the Cookie header.')
    sys.exit(1)

if not accepted_terms_of_use:
    sys.stderr.write('Please accept the terms of use:\n')
    sys.stderr.write('In the source, read the terms and change "accepted_terms_of_use" to True.\n')
    sys.exit(3)

course = sys.argv[1]
labn = sys.argv[2]
question = sys.argv[3]

raw_cookies = open('cookie.txt', 'rt').read().split('; ')
cookies = {}
for cookie in raw_cookies:
    cookies[cookie.split('=')[0]] = cookie.split('=')[1].strip()

if not os.path.isdir(cacheFolder):
    os.mkdir(cacheFolder)

cacheFile = cacheFolder + md5(bytes('labassignments-{}-{}-{}'.format(base_url, year, course), 'utf-8')).hexdigest()
if useCache and os.path.isfile(cacheFile):
    names = open(cacheFile).read()
else:
    tries = 0
    if verbose:
        sys.stderr.write('Getting course page...\n')
    while True:
        try:
            names = get('{}/{}/courses/{}/labassignments'.format(base_url, year, course), cookies=cookies, timeout=timeout).text
            if slowly > 0.0001:
                time.sleep(slowly)
            break
        except requests.exceptions.Timeout:
            if verbose:
                sys.stderr.write('Timeout getting {} page, retrying\n'.format(course))
            if tries >= retries:
                sys.stderr.write('Error downloading page. Giving up after {} tries.\n'.format(tries))
                sys.exit(2)
            tries += 1

    if writeCache:
        f = open(cacheFile, 'w')
        f.write(names)
        f.close()

for name_line in names.split('\n'):
    if '<li class="level1"><div class="li">' not in name_line or 'href="/2017-2018/students/' not in name_line:
        continue

    name = name_line.split('href="/2017-2018/students/')[1]
    name = name.split('/')[0]
    if verbose:
        sys.stderr.write('Processing {}\n'.format(name))

    personurl = '{}/{}/students/{}/{}/lab{}'.format(base_url, year, name, course, labn)
    cacheFile = '{}/{}'.format(cacheFolder, md5(bytes(personurl, 'utf-8')).hexdigest())
    if useCache and os.path.isfile(cacheFile):
        page = open(cacheFile).read()
    else:
        tries = 0
        while True:
            try:
                page = get(personurl, cookies=cookies)
                if slowly > 0.0001:
                    time.sleep(slowly)
                if page.status_code != 200:
                    if verbose:
                        sys.stderr.write('{} does not have this page.\n'.format(name))
                break
            except requests.exceptions.Timeout:
                if tries >= retries:
                    if verbose:
                        sys.stderr.write('Timeout getting {}\'s page, retrying\n'.format(name))
                    sys.stderr.write('Error downloading page. Giving up after {} tries.\n'.format(tries))
                    sys.exit(2)
                tries += 1

        if writeCache:
            f = open(cacheFile, 'w')
            f.write(page.text)
            f.close()

    page = page.text

    lines = page.split('\n')
    started = False
    for line in lines:
        if 'class="sectionedit' in line:
            headingtext = line[line.index('>'):]
            headingtext = headingtext[:headingtext.index('<')]
            headingtext = headingtext[0:15] # Because after that, we can assume it's just a random number in the title
            if (question + ' ' in headingtext
                    or question + '.' in headingtext
                    or ' ' + question in headingtext
                    or 'q' + question in headingtext.lower()
                    or '>' + question in headingtext
                    ):

                # prevent e.g. "Question 12: asdf" as matching "1", by checking whether the preceding or following character is also a number.
                if line[line.index(question)+len(question)] in [str(i) for i in range(0, 10)] \
                        or line[line.index(question)-1] in [str(i) for i in range(0, 10)]:
                    if verbose:
                        sys.stderr.write('Skipping because false-positive detection went off on line: ')
                        sys.stderr.write(line + '\n')
                    continue

                started = 1
                print('<hr><a href="{}">{}</a>:<div class=garbl>'.format(personurl, name))
                first = True

        if started:
            if started > 1 and 'class="sectionedit' in line:
                started = False
                print('</div></div></div></div></div><hr>')
            else:
                print(line.replace('img src="/_media', 'img src="{}/_media'.format(base_url)))
                started += 1
    sys.stdout.flush()

print('<style>.garbl { background-color: #eef; margin-bottom: 50px; }</style>')
print('<meta charset="utf-8">')

