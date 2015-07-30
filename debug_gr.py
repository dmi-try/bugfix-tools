#!/usr/bin/env python
import argparse
from pygerrit.rest import GerritRestAPI
import datetime

cachedir = "~/.launchpadlib/cache/"
report_date = '2015-07-25'
start_date = '2015-06-22'
branch = 'master'

parser = argparse.ArgumentParser(description='Debug LP bugs fixes stats.')
parser.add_argument('user', type=str, help="Mirantis username")
args = parser.parse_args()
user = args.user
print "Checking user %s@mirantis.com" % user

one_week_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=1)
two_weeks_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=2)

projects = ['^stackforge/fuel-.*', '^stackforge/python-fuel.*']
template = '/changes/?q=project:%s+owner:".*<%s@mirantis.com>"+message:"bug:+"'
url = 'https://review.openstack.org/#/c/%s'

rest = GerritRestAPI(url='https://review.openstack.org')

total_merged = 0
total_open = 0

for project in projects:
    changes = rest.get(template % (project, user))
    for change in changes:
          if change['branch'] != branch or change['status'] == 'ABANDONED':
              continue
          if change['created'] > start_date and change['created'] < report_date:
              if change['status'] == 'MERGED':
                  print "Merged: %s" % (url % change['_number'])
                  total_merged += 1
              else:
                  print "Open: %s" % (url % change['_number'])
                  total_open += 1

print "TOTAL MERGED: %s" % total_merged
print "TOTAL OPEN: %s" % total_open

