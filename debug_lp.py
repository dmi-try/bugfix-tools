#!/usr/bin/env python
import pickle
import argparse
from launchpadlib.launchpad import Launchpad

cachedir = "~/.launchpadlib/cache/"
report_date = '2015-07-30'
start_date = '2015-06-22'
ms = '7.0'

parser = argparse.ArgumentParser(description='Debug LP bugs fixes stats.')
parser.add_argument('user', type=str, help="Mirantis username")
parser.add_argument("-d", "--debug", help="Additional debug", action="store_true")
parser.add_argument("-l", "--login", help="Login", action="store_true")
args = parser.parse_args()
user = args.user

if args.login:
    launchpad = Launchpad.login_with('kpi debug', 'production', cachedir)
else:
    launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)

print "Checking user %s@mirantis.com" % user
p = launchpad.people.getByEmail(email="%s@mirantis.com" % user)
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
        print "Found bug assigned to %s: %s" % (user, bug.web_link)
        for task in bug.bug.bug_tasks:
            milestone = '{0}'.format(task.milestone_link).split('/')[-1]
            if milestone == ms:
                if (bug.status == "Fix Committed" and str(task.date_fix_committed) > start_date \
                        and str(task.date_fix_committed) < report_date) or \
                      (bug.status == "Fix Released" and str(task.date_fix_released) > start_date \
                      and str(task.date_fix_released) < report_date):
                          print "FIXED %s %s" % (task.importance, bug.web_link)
                          fixed += 1

print "TOTAL FIXED in %s: %s" % (ms, fixed)

