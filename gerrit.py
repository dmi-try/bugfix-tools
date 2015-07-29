from pygerrit.rest import GerritRestAPI
import datetime

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
    def __init__(self, users):
        self.users = users
        self.rest = GerritRestAPI(url='https://review.openstack.org')

    def fixes(self, start_date, report_date, branch):
        fixes = {}
        one_week_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=1)
        two_weeks_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=2)

        projects = ['^stackforge/fuel-.*', '^stackforge/python-fuel.*']
        template = '/changes/?q=project:%s+owner:".*<%s@mirantis.com>"+message:"bug:+"'
        url = 'https://review.openstack.org/#/c/%s'

        for user in self.users:
            fixes[user] = {}
            fixes[user]['merged'] = []
            fixes[user]['merged_this_week'] = []
            fixes[user]['merged_last_week'] = []
            fixes[user]['open'] = []
            fixes[user]['open_this_week'] = []
            fixes[user]['open_last_week'] = []
            for project in projects:
                try:
                    changes = self.rest.get(template % (project, user))
                except:
                    changes = []
                for change in changes:
                    if change['branch'] != branch or change['status'] == 'ABANDONED':
                        continue
                    if change['created'] > start_date and change['created'] < report_date:
                        if change['status'] == 'MERGED':
                            fixes[user]['merged'].append(url % change['_number'])
                            if change['updated'] > str(one_week_ago_date):
                                fixes[user]['merged_this_week'].append(url % change['_number'])
                            elif change['created'] > str(two_weeks_ago_date):
                                fixes[user]['merged_last_week'].append(url % change['_number'])
                        else:
                            fixes[user]['open'].append(url % change['_number'])
                            if change['created'] > str(one_week_ago_date):
                                fixes[user]['open_this_week'].append(url % change['_number'])
                            elif change['created'] > str(two_weeks_ago_date):
                                fixes[user]['open_last_week'].append(url % change['_number'])
        return fixes


if __name__ == '__main__':
    for group in engineers:
        print "\n#####################"
        print "# %s" % group
        ppl = GerritUsers(engineers[group])
        fixes = ppl.fixes(start_date, report_date, branch)

