from launchpadlib.launchpad import Launchpad
import datetime

class LpUsers:
    def __init__(self, users, cachedir = "~/.launchpadlib/cache/", login = False):
        self.users = users
        if login:
            self.launchpad = Launchpad.login_with('kpi bugfix', 'production', cachedir)
        else:
            self.launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)

    def bugs(self, start_date, report_date, ms, projects = ['fuel', 'mos']):
        bugs = {}

        for user in self.users:
            bugs[user] = []
            # Don't fail if user does not exist in LP. We'll just put 0 bug fixed for such users.
            try:
                p = self.launchpad.people.getByEmail(email="%s@mirantis.com" % user)
                list_of_bugs = p.searchTasks(status=["New", "Incomplete", "Confirmed", "Triaged",
                                         "In Progress", "Fix Committed", "Fix Released"],
                                     assignee=p,
                                     modified_since=start_date)
            except:
                continue
            for bug in list_of_bugs:
                if bug.milestone == None:
                    continue
                project = '{0}'.format(bug.milestone).split('/')[-3]
                if project not in projects:
                    continue
                milestone = '{0}'.format(bug.milestone).split('/')[-1]
                if milestone == ms:
                    if bug.status == "In Progress":
                        change_date = bug.date_in_progress
                    if bug.status in ["Fix Committed", "Fix Released"]:
                        change_date = bug.date_fix_committed
                    if bug.status == "Confirmed":
                        change_date = bug.date_confirmed
                    if bug.status == "Triaged":
                        change_date = bug.date_triaged
                    if bug.status == "Incomplete":
                        change_date = bug.date_incomplete
                    if bug.status == "New":
                        change_date = bug.date_created
                    if bug.status in ["Won't Fix", "Invalid"]:
                        change_date = bug.date_closed
                    if change_date == None:
                        print "ERROR FOUND: %s %s %s" % (bug.web_link, bug, bug.status)
                        continue
                    if change_date > start_date and change_date < report_date:
                        if not any(tmp['web_link'] == bug.web_link for tmp in bugs[user]):
                            mybug = {}
                            mybug['web_link'] = bug.web_link
                            mybug['importance'] = bug.importance
                            mybug['tags'] = bug.bug.tags
                            mybug['change_date'] = change_date
                            mybug['status'] = bug.status
                            bugs[user].append(mybug)

        return bugs

