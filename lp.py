from launchpadlib.launchpad import Launchpad
import datetime

print datetime.datetime.now()

start_date = '2015-06-22'
report_date = '2015-07-25'
ms = '7.0'

engineers = {}
engineers['bugfix'] = ['adidenko', 'akislitsky', 'rprikhodchenko', 'agordeev',
                 'omolchanov', 'ddmitriev', 'dilyin', 'vsharshov']
engineers['service'] = ['mgrygoriev', 'sflorczak', 'pstefanski', 'tjaroszewski']
engineers['partner'] = ['aarzhanov', 'igajsin']

class LpUsers:
    def __init__(self, users, cachedir = "~/.launchpadlib/cache/"):
        self.users = users
        self.launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)

    def bugs(self, start_date, report_date, ms):
        bugs = {}
        one_week_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=1)
        two_weeks_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=2)

        for user in self.users:
            bugs[user] = {}
            bugs[user]['fixed'] = []
            bugs[user]['closed'] = []
            try:
                p = self.launchpad.people.getByEmail(email="%s@mirantis.com" % user)
                list_of_bugs = p.searchTasks(status=["New", "Incomplete", "Invalid",
                                                 "Won't Fix", "Confirmed", "Triaged",
                                                 "In Progress", "Fix Committed",
                                                 "Fix Released", "Opinion", "Expired"],
                                     modified_since=start_date,
                                     milestone="https://api.launchpad.net/1.0/fuel/+milestone/%s" % ms)
            except:
                continue

            for bug in list_of_bugs:
                bug_milestone = '{0}'.format(bug.milestone).split('/')[-1]
                if bug.assignee is not None and bug.assignee.name == user and bug_milestone == ms:
                    for task in bug.bug.bug_tasks:
                        milestone = '{0}'.format(task.milestone_link).split('/')[-1]
                        if milestone == ms:
                            if (bug.status == "Fix Committed" and str(task.date_fix_committed) > start_date \
                                    and str(task.date_fix_committed) < report_date) or \
                                  (bug.status == "Fix Released" and str(task.date_fix_released) > start_date \
                                  and str(task.date_fix_released) < report_date):
                                bugs[user]['fixed'].append(bug.web_link)
                                #print "Fixed:  %s" % bug.web_link
                            #if bug.status in ["Invalid", "Won't Fix"]:
                                #bugs[user]['closed'].append(bug.web_link)
                                #print "Closed: %s" % bug.web_link

        return bugs

if __name__ == '__main__':
    for group in engineers:
        print "\n#####################"
        print "# %s" % group
        ppl = LpUsers(engineers[group])
        bugs = ppl.bugs(start_date, report_date, ms)
        for user in bugs:
            print len(bugs[user]['fixed'])
            for bug in bugs[user]['fixed']:
                print bug

