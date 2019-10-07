#!/usr/bin/env python
# coding: utf-8

import requests
import pytz
import icalendar
import argparse
import sys
from bs4 import BeautifulSoup
from datetime import datetime

# optionally enable cache (useful for testing script repeatedly)
#import requests_cache
#requests_cache.install_cache('/tmp/sportzcal-cache', backend='sqlite', expire_after=900)

def page_to_ical(html, suppress_dtstamp=False, verbose=False):
    soup = BeautifulSoup(html, 'lxml')

    cal = icalendar.Calendar()
    cal.add('prodid', '-//Nils Steinger//Uni Passau Sportzentrum iCal generator (unofficial)//DE')
    cal.add('version', '2.0')

    content = soup.find('div', attrs={'id': 'bs_content'})
    title = content.find('', attrs={'class': 'bs_head'}).get_text()
    if verbose:
        sys.stderr.write('Course title: %s\n' % (title))

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
        location_url = event.find('a').attrs['href']
        location_name = event.find('a').get_text()
        for loctag in content.find_all('a', attrs={'href': location_url}):
            locparent = loctag.parent
            if 'class' in locparent.attrs and 'bs_text' in locparent.attrs['class']:
                location_name = locparent.get_text()
        calevent = icalendar.Event()
        calevent.add('summary', title)
        if not suppress_dtstamp:
            calevent.add('dtstamp', datetime.now())
        calevent.add('dtstart', starttime)
        calevent.add('dtend', endtime)
        calevent['location'] = icalendar.vText(location_name)
        calevent['contact'] = organizers
        cal.add_component(calevent)

    if verbose:
        sys.stderr.write('%d events processed\n' % (len(cal.subcomponents)))

    return cal.to_ical()

def main():
    parser = argparse.ArgumentParser(description='Generate an iCalendar file from Sports Centre course dates')
    parser.add_argument('courseinfo_url',
            help='URL of the course info page, e.g. https://online.sportz.uni-passau.de/cgi/webpage.cgi?kursinfo=765C3A7B')
    parser.add_argument('--output-file', '-o',
            type=argparse.FileType('w'), default=sys.stdout,
            help='File to write the ical data to. Default to stdout.')
    parser.add_argument('--no-dtstamp', '-t',
            action='store_true',
            help='Don\'t add DTSTAMP attribute to output (not standard-compliant!). Allows for comparing output from multiple runs.')
    parser.add_argument('--verbose', '-v',
            action='store_true',
            help='Print details about processed data to stderr.')

    args = parser.parse_args()

    if args.verbose:
        sys.stderr.write('Downloading URL: %s\n' % (args.courseinfo_url))
    response = requests.get(args.courseinfo_url)
    response.raise_for_status()

    ical = page_to_ical(response.content, args.no_dtstamp, args.verbose)

    args.output_file.write(ical.decode('utf8'))

if __name__ == '__main__':
    main()
