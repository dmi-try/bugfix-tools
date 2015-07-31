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

list_of_bugs = p.searchTasks(status=["In Progress", "Fix Committed", "Fix Released"],
                     modified_since=start_date)

fixed = 0
for bug in list_of_bugs:
    if bug.milestone == None:
        continue
    project = '{0}'.format(bug.milestone).split('/')[-3]
    bug_milestone = '{0}'.format(bug.milestone).split('/')[-1]
    if project not in ['fuel', 'mos']:
        continue
    if args.debug:
        print "Checking bug %s, project %s, milestone %s, assignee %s" % (bug.web_link, project, bug_milestone, bug.assignee.name)
    if bug.assignee is not None and bug.assignee.name == p.name:
        if args.debug:
            print "Found bug assigned to %s: %s" % (user, bug.web_link)
        for task in bug.bug.bug_tasks:
            milestone = '{0}'.format(task.milestone_link).split('/')[-1]
            if milestone == ms:
                   if bug.status == "Fix Committed":
                       fixed_date = str(task.date_fix_committed)
                   if bug.status == "Fix Released":
                       fixed_date = str(task.date_fix_released)
                   if fixed_date > start_date and fixed_date < report_date:
                       info = str(task.importance)
                       if 'tricky' in bug.bug.tags:
                           info.append(', Tricky')
                       print "%s %s" % (info, bug.web_link)
                       fixed += 1

print "TOTAL FIXED between %s and %s: %s" % (start_date, report_date, fixed)

