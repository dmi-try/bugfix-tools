#!/usr/bin/env python
import argparse
from pygerrit.rest import GerritRestAPI
import datetime
import re


parser = argparse.ArgumentParser(description='Debug LP bugs fixes stats.')
parser.add_argument('user', type=str, help="Mirantis username")
parser.add_argument("-d", "--debug", help="Additional debug", action="store_true")
parser.add_argument("-l", "--login", help="Login", action="store_true")
parser.add_argument('--start-date', type=str, help="Report start date.",
        default = datetime.datetime.now().strftime("%Y-%m-%d"))
parser.add_argument('--report-date', type=str, help="Report end date.",
        default = datetime.datetime.now().strftime("%Y-%m-%d"))
args = parser.parse_args()
user = args.user
start_date = args.start_date
report_date = args.report_date

print "Checking user %s@mirantis.com" % user

one_week_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=1)
two_weeks_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=2)


gerrits = ['https://review.openstack.org', 'https://review.fuel-infra.org']
template = '/changes/?q=project:%s+owner:".*<%s@mirantis.com>"+message:"bug:+"'
projects = {}
url ={}
projects['https://review.openstack.org'] = ['^openstack/fuel-.*', '^openstack/python-fuel.*']
projects['https://review.fuel-infra.org'] = ['^.*']
url['https://review.openstack.org'] = 'https://review.openstack.org/#/c/%s'
url['https://review.fuel-infra.org'] = 'https://review.fuel-infra.org/#/c/%s'
branch = {}
branch['https://review.openstack.org'] = 'master'
branch['https://review.fuel-infra.org'] = '.*'

total_merged = 0
total_open = 0

for gerrit in gerrits:
    if args.debug:
        print "Checking %s gerrit" % gerrit
    rest = GerritRestAPI(url=gerrit)
    for project in projects[gerrit]:
        print "Getting changes for user"
        try:
            changes = rest.get(template % (project, user), timeout=1)
        except:
            changes = []
        for change in changes:
            if args.debug:
                print "checking %s review" % (url[gerrit] % change['_number'])
            if not re.search(branch[gerrit], change['branch']) or change['status'] == 'ABANDONED':
                continue
            if change['created'] > start_date and change['created'] < report_date:
                if change['status'] == 'MERGED':
                    print "Merged: %s" % (url[gerrit] % change['_number'])
                    total_merged += 1
                else:
                    print "Open: %s" % (url[gerrit] % change['_number'])
                    total_open += 1

print "TOTAL MERGED: %s" % total_merged
print "TOTAL OPEN: %s" % total_open

