from pygerrit.rest import GerritRestAPI
import datetime
import pickle
import re

start_date = '2015-06-22'
report_date = '2015-07-25'
branch = 'master'

engineers = {}
engineers['bugfix'] = ['adidenko', 'akislitsky', 'rprikhodchenko', 'agordeev',
                 'omolchanov', 'ddmitriev', 'dilyin', 'vsharshov']
engineers['service'] = ['mgrygoriev', 'sflorczak', 'pstefanski', 'tjaroszewski']
engineers['partner'] = ['aarzhanov', 'igajsin']

##########################
class GerritUsers:
    def __init__(self, users, gerrit = 'https://review.openstack.org',
            projects = ['^stackforge/fuel-.*', '^stackforge/python-fuel.*'],
            template = '/changes/?q=project:%s+owner:".*<%s@mirantis.com>"+message:"bug:+"',
            url = 'https://review.openstack.org/#/c/%s'):
        self.users = users
        self.rest = GerritRestAPI(url=gerrit)
        self.projects = projects
        self.template = template
        self.url = url

    def fixes(self, start_date, report_date, branch):
        fixes = {}
        last_sun = report_date - datetime.timedelta(days=report_date.weekday()) + \
                datetime.timedelta(days=6, weeks=-1)
        prelast_sun = last_sun - datetime.timedelta(weeks=1)

        for user in self.users:
            fixes[user] = {}
            fixes[user]['merged'] = []
            fixes[user]['merged_this_week'] = []
            fixes[user]['merged_last_week'] = []
            fixes[user]['open_this_week'] = []

            for project in self.projects:
                try:
                    changes = self.rest.get(self.template % (project, user))
                except:
                    changes = []
                for change in changes:
                    if not re.search(branch, change['branch']) or change['status'] == 'ABANDONED':
                        continue
                    if change['created'] > str(start_date) and change['created'] < str(report_date):
                        if change['status'] == 'MERGED':
                            fixes[user]['merged'].append(self.url % change['_number'])
                            if change['updated'][:10] > str(last_sun)[:10]:
                                fixes[user]['merged_this_week'].append(self.url % change['_number'])
                            elif change['created'][:10] > str(prelast_sun)[:10]:
                                fixes[user]['merged_last_week'].append(self.url % change['_number'])
                        else:
                            if change['created'][:10] > str(last_sun)[:10]:
                                fixes[user]['open_this_week'].append(self.url % change['_number'])

        return fixes

if __name__ == '__main__':
    for group in engineers:
        print "\n#####################"
        print "# %s" % group
        ppl = GerritUsers(engineers[group])
        fixes = ppl.fixes(start_date, report_date, branch)

