#!/usr/bin/env python
import datetime
import argparse
from launchpadlib.launchpad import Launchpad

cachedir = "~/.launchpadlib/cache/"
ms = '7.0'

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

if args.login:
    launchpad = Launchpad.login_with('kpi debug', 'production', cachedir)
else:
    launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)

if args.debug:
    print "Checking user %s@mirantis.com" % user

p = launchpad.people.getByEmail(email="%s@mirantis.com" % user)

if args.debug:
    print "Found user %s (%s)" % (p.display_name, p.name)

list_of_bugs = p.searchTasks(status=["New", "Incomplete", "Invalid",
                                 "Won't Fix", "Confirmed", "Triaged",
                                 "In Progress", "Fix Committed",
                                 "Fix Released", "Opinion", "Expired"],
                     modified_since=start_date,
                     milestone="https://api.launchpad.net/1.0/fuel/+milestone/%s" % ms)

fixed = 0
for bug in list_of_bugs:
    bug_milestone = '{0}'.format(bug.milestone).split('/')[-1]
    if args.debug:
        print "Checking bug %s, milestone %s, assignee %s" % (bug.web_link, bug_milestone, bug.assignee.name)
    if bug.assignee is not None and bug.assignee.name == p.name:
        if args.debug:
            print "Found bug assigned to %s: %s" % (user, bug.web_link)
        for task in bug.bug.bug_tasks:
            milestone = '{0}'.format(task.milestone_link).split('/')[-1]
            if milestone == ms:
                if (bug.status == "Fix Committed" and str(task.date_fix_committed) > start_date \
                        and str(task.date_fix_committed) < report_date) or \
                      (bug.status == "Fix Released" and str(task.date_fix_released) > start_date \
                      and str(task.date_fix_released) < report_date):
                          print "FIXED %s %s" % (task.importance, bug.web_link)
                          if 'kilo' in bug.bug.tags:
                              print 'KILO'
                          fixed += 1

print "TOTAL FIXED between %s and %s: %s" % (start_date, report_date, fixed)

