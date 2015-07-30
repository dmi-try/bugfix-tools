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

    def bugs(self, start_date, report_date, ms, cachedir = "~/.launchpadlib/cache_reports/"):
        bugs = {}
        one_week_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=1)
        two_weeks_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=2)

        for user in self.users:
            bugs[user] = {}
            bugs[user]['high'] = []
            bugs[user]['other'] = []
            # Getting info from LP may take forever, so let's use something like cache
            cache_filename = "%s/%s_%s_%s_%s.lp" % (cachedir, user, report_date, start_date, ms)
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
                                                 "In Progress", "Fix Committed",
                                                 "Fix Released", "Opinion", "Expired"],
                                     modified_since=start_date,
                                     milestone="https://api.launchpad.net/1.0/fuel/+milestone/%s" % ms)
            except:
                continue
            for bug in list_of_bugs:
                bug_milestone = '{0}'.format(bug.milestone).split('/')[-1]
                if bug.assignee is not None and bug.assignee.name == p.name:
                    for task in bug.bug.bug_tasks:
                        milestone = '{0}'.format(task.milestone_link).split('/')[-1]
                        if milestone == ms:
                            if (bug.status == "Fix Committed" and str(task.date_fix_committed) > start_date \
                                    and str(task.date_fix_committed) < report_date) or \
                                  (bug.status == "Fix Released" and str(task.date_fix_released) > start_date \
                                  and str(task.date_fix_released) < report_date):
                                      if bug.web_link not in bugs[user]['high'] and \
                                          bug.web_link not in bugs[user]['other']:
                                          if task.importance in ['High', 'Critical']:
                                              bugs[user]['high'].append(bug.web_link)
                                          else:
                                              bugs[user]['other'].append(bug.web_link)

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

