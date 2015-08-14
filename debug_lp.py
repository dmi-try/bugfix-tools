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

if args.uid:
    print p.name
    sys.exit(0)

if args.debug:
    print "Found user %s (%s)" % (p.display_name, p.name)

list_of_bugs = p.searchTasks(status=["In Progress", "Fix Committed", "Fix Released"],
                     assignee=p,
                     modified_since=start_date)

if args.debug:
    print "Got %s LP tasks for %s" % (len(list_of_bugs), p.name)

fixed = []
inprogress = []
for bug in list_of_bugs:
    if bug.milestone == None:
        continue
    project = '{0}'.format(bug.milestone).split('/')[-3]
    bug_milestone = '{0}'.format(bug.milestone).split('/')[-1]
    if project not in ['fuel', 'mos']:
        continue
    if args.debug:
        print "Checking bug %s, project %s, milestone %s, assignee %s" % (bug.web_link, project, bug_milestone, bug.assignee.name)
    if args.debug:
        print "Found bug assigned to %s: %s" % (user, bug.web_link)
    milestone = '{0}'.format(bug.milestone_link).split('/')[-1]
    if milestone == ms:
        if bug.status == "In Progress":
            fixed_date = str(bug.date_in_progress)
        if bug.status == "Fix Committed":
            fixed_date = str(bug.date_fix_committed)
        if bug.status == "Fix Released":
            fixed_date = str(bug.date_fix_released)
        if fixed_date > start_date and fixed_date < report_date:
            if bug.web_link not in fixed and bug.web_link not in inprogress:
                info = str(bug.importance)
                if 'tricky' in bug.bug.tags:
                    info.append(', Tricky')
                print "[%s] %s %s" % (bug.status, info, bug.web_link)
                if bug.status == "In Progress":
                    inprogress.append(bug.web_link)
                else:
                    fixed.append(bug.web_link)

print "TOTAL IN PROGRESS between %s and %s : %s" % (start_date, report_date, len(inprogress))
print "TOTAL FIXED between %s and %s       : %s" % (start_date, report_date, len(fixed))

