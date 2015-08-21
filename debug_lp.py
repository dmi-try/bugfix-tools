#!/usr/bin/env python
import datetime
import argparse
import sys
from launchpadlib.launchpad import Launchpad

cachedir = "~/.launchpadlib/cache/"
ms = '7.0'

parser = argparse.ArgumentParser(description='Debug LP bugs fixes stats.')
parser.add_argument('user', type=str, help="Mirantis username")
parser.add_argument("-d", "--debug", help="Additional debug", action="store_true")
parser.add_argument("-l", "--login", help="Login", action="store_true")
parser.add_argument("-u", "--uid", help="Get LP user ID", action="store_true")
parser.add_argument('--start-date', type=str, help="Report start date.",
        default = '2015-06-22')
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

if args.uid:
    print p.name
    sys.exit(0)

if args.debug:
    print "Found user %s (%s)" % (p.display_name, p.name)

list_of_bugs = p.searchTasks(status=["In Progress", "Fix Committed", "Fix Released",
    "New", "Confirmed", "Triaged"],
                     assignee=p,
                     modified_since=start_date)

if args.debug:
    print "Got %s LP tasks for %s" % (len(list_of_bugs), p.name)

fixed = []
inprogress = []
assigned = []

for bug in list_of_bugs:
    if bug.milestone == None:
        continue
    project = '{0}'.format(bug.milestone).split('/')[-3]
    bug_milestone = '{0}'.format(bug.milestone).split('/')[-1]
    if project not in ['fuel', 'mos']:
        continue
    if args.debug:
        print "Checking bug %s, project %s, milestone %s, assignee %s, status %s" % \
                (bug, project, bug_milestone, bug.assignee.name, bug.status)
    if bug_milestone == ms:
        if bug.status == "In Progress":
            fixed_date = bug.date_in_progress
        if bug.status == "Fix Committed":
            fixed_date = bug.date_fix_committed
        if bug.status == "Fix Released":
            fixed_date = bug.date_fix_released
        if bug.status in ["New", "Confirmed", "Triaged"]:
            assigned.append(bug)
        elif str(fixed_date) > start_date and str(fixed_date) < report_date:
            if bug not in fixed and bug not in inprogress:
                if bug.status == "In Progress":
                    inprogress.append(bug)
                else:
                    fixed.append(bug)

line = "--------------------------------------------"
print line
for bug in fixed:
    print "[%s] [%s] %s - %s" % (bug.status, ', '.join(bug.bug.tags), bug.web_link, fixed_date)
print line
for bug in inprogress:
    print "[%s] [%s] %s - %s" % (bug.status, ', '.join(bug.bug.tags), bug.web_link, fixed_date)
print line
for bug in assigned:
    print "[%s] [%s] %s" % (bug.status, ', '.join(bug.bug.tags), bug.web_link)

print line
print "TOTAL ASSIGNED                                      : %s" % len(assigned)
print "TOTAL IN PROGRESS between %s and %s : %s" % (start_date, report_date, len(inprogress))
print "TOTAL FIXED between %s and %s       : %s" % (start_date, report_date, len(fixed))

