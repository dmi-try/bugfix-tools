from launchpadlib.launchpad import Launchpad
import datetime
import pickle

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
    def __init__(self, users, cachedir = "~/.launchpadlib/cache/", login = False):
        self.users = users
        if login:
            self.launchpad = Launchpad.login_with('kpi bugfix', 'production', cachedir)
        else:
            self.launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)

    def bugs(self, start_date, report_date, ms, cachedir = "~/.launchpadlib/cache_reports/", projects = ['fuel', 'mos']):
        bugs = {}
        one_week_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=1)
        two_weeks_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=2)

        for user in self.users:
            bugs[user] = []
            # Getting info from LP may take forever, so let's use something like cache
            cache_filename = "%s/%s_%s_%s_%s.lpc" % (cachedir, user, report_date, start_date, ms)
            try:
                cache_file = open(cache_filename, 'rb')
                bugs[user] = pickle.load(cache_file)
                cache_file.close()
                continue
            except:
                pass
            # Don't fail if user does not exist in LP. We'll just put 0 bug fixed for such users.
            try:
                p = self.launchpad.people.getByEmail(email="%s@mirantis.com" % user)
                list_of_bugs = p.searchTasks(status=["New", "Incomplete", "Invalid",
                                         "Won't Fix", "Confirmed", "Triaged",
                                         "In Progress", "Fix Committed", "Fix Released"],
                                     modified_since=start_date)
            except:
                continue
            for bug in list_of_bugs:
                if bug.milestone == None:
                    continue
                project = '{0}'.format(bug.milestone).split('/')[-3]
                bug_milestone = '{0}'.format(bug.milestone).split('/')[-1]
                if project not in projects:
                    continue
                if bug.assignee is not None and bug.assignee.name == p.name:
                    for task in bug.bug.bug_tasks:
                        milestone = '{0}'.format(task.milestone_link).split('/')[-1]
                        if milestone == ms:
                            if bug.status == "In Progress":
                                change_date = str(task.date_in_progress)
                            if bug.status in ["Fix Committed", "Fix Released"]:
                                change_date = str(task.date_fix_committed)
                            if bug.status == "Confirmed":
                                change_date = str(task.date_confirmed)
                            if bug.status == "Triaged":
                                change_date = str(task.date_triaged)
                            if bug.status == "Incomplete":
                                change_date = str(task.date_incomplete)
                            if bug.status == "New":
                                change_date = str(task.date_created)
                            if bug.status in ["Won't Fix", "Invalid"]:
                                change_date = str(task.date_closed)
                            if change_date > start_date and change_date < report_date:
                                if not any(tmp['web_link'] == bug.web_link for tmp in bugs[user]):
                                    mybug = {}
                                    mybug['web_link'] = bug.web_link
                                    mybug['importance'] = task.importance
                                    mybug['tags'] = bug.bug.tags
                                    mybug['change_date'] = change_date
                                    mybug['status'] = bug.status
                                    bugs[user].append(mybug)

            # Getting info from LP may take forever, so let's use something like cache
            try:
                cache_file = open(cache_filename, 'wb')
                pickle.dump(bugs[user], cache_file)
                cache_file.close()
            except:
                pass

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

