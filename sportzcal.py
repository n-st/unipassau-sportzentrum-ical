#!/usr/bin/env python
# coding: utf-8

import requests
import pytz
import icalendar
from bs4 import BeautifulSoup
from datetime import datetime

# optionally enable cache (useful for testing script repeatedly)
#import requests_cache
#requests_cache.install_cache('/tmp/sportzcal-cache', backend='sqlite', expire_after=900)

req = requests.get('https://online.sportz.uni-passau.de/cgi/webpage.cgi?kursinfo=765C3A7B')

soup = BeautifulSoup(req.content, 'lxml')

cal = icalendar.Calendar()
cal.add('prodid', '-//Nils Steinger//Uni Passau Sportzentrum iCal generator (unofficial)//DE')
cal.add('version', '2.0')

content = soup.find('div', attrs={'id': 'bs_content'})
title = content.find('', attrs={'class': 'bs_head'}).get_text()
print(title)

organames = content.find('', attrs={'class': 'bs_text'}).get_text()
organizers = icalendar.vText(organames)

calevents = []
eventtable = content.find('table')
if not eventtable:
    raise Exception('The Sports Centre hasn\'t provided a list of dates for this course.')
events = content.find('table').find_all('tr')
for event in events:
    edate = event.find_all('td')[1].get_text()
    etimes = event.find_all('td')[2].get_text().split('-')
    starttime = datetime.strptime(edate+etimes[0], '%d.%m.%Y%H.%M')
    endtime = datetime.strptime(edate+etimes[1], '%d.%m.%Y%H.%M')
    starttime = pytz.timezone('Europe/Berlin').localize(starttime)
    endtime = pytz.timezone('Europe/Berlin').localize(endtime)
    locurl = event.find('a').attrs['href']
    locstr = event.find('a').get_text()
    for loctag in content.find_all('a', attrs={'href': locurl}):
        locparent = loctag.parent
        if 'class' in locparent.attrs and 'bs_text' in locparent.attrs['class']:
            locstr = locparent.get_text()
    calevent = icalendar.Event()
    calevent.add('summary', title)
    calevent.add('dtstamp', datetime.now())
    calevent.add('dtstart', starttime)
    calevent.add('dtend', endtime)
    calevent['location'] = icalendar.vText(locstr)
    calevent['contact'] = organizers
    cal.add_component(calevent)

open('/tmp/test.ical', 'w').write(cal.to_ical().decode('utf8'))
