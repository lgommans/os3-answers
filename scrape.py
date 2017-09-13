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
base_url = 'https://www.os3.nl/2017-2018'

import sys, time
from requests import get

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

names = get('{}/courses/{}/labassignments'.format(base_url, course), cookies=cookies).text
if slowly > 0.0001:
    time.sleep(slowly)

for name_line in names.split('\n'):
    if '<li class="level1"><div class="li">' not in name_line or 'href="/2017-2018/students/' not in name_line:
        continue

    name = name_line.split('href="/2017-2018/students/')[1]
    name = name.split('/')[0]
    if verbose:
        sys.stderr.write('Processing {}\n'.format(name))

    page = get('{}/students/{}/{}/lab{}'.format(base_url, name, course, labn), cookies=cookies)
    if slowly > 0.0001:
        time.sleep(slowly)
    if page.status_code != 200:
        if verbose:
            sys.stderr.write('{} does not have this page.\n'.format(name))
        continue

    page = page.text

    lines = page.split('\n')
    started = False
    for line in lines:
        if 'class="sectionedit' in line:
            headingtext = line[line.index('>'):]
            headingtext = headingtext[:headingtext.index('<')]
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
                print('<hr>{}:<div class=garbl>'.format(name))
                first = True

        if started:
            if started > 1 and 'class="sectionedit' in line:
                started = False
                print('</div></div></div></div></div><hr>')
            else:
                print(line)
                started += 1
    sys.stdout.flush()

print('<style>.garbl { background-color: #eef; margin-bottom: 50px; }</style>')

