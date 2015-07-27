from pygerrit.rest import GerritRestAPI
import datetime
import argparse

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

    def fixes(self, start_date, report_date, branch):
        fixes = {}
        one_week_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=1)
        two_weeks_ago_date = datetime.datetime.strptime(report_date, '%Y-%m-%d') - datetime.timedelta(weeks=2)

        rest = GerritRestAPI(url='https://review.openstack.org')
        projects = ['^stackforge/fuel-.*', '^stackforge/python-fuel.*']
        template = '/changes/?q=project:%s+owner:".*<%s@mirantis.com>"+message:"bug:+"'

        for user in self.users:
            fixes[user] = {}
            fixes[user]['merged'] = 0
            fixes[user]['merged_this_week'] = 0
            fixes[user]['merged_last_week'] = 0
            fixes[user]['open'] = 0
            fixes[user]['open_this_week'] = 0
            fixes[user]['open_last_week'] = 0
            for project in projects:
              changes = rest.get(template % (project, user))
              for change in changes:
                  if change['branch'] != branch or change['status'] == 'ABANDONED':
                      continue
                  if change['created'] > start_date and change['created'] < report_date:
                      if change['status'] == 'MERGED':
                          fixes[user]['merged'] += 1
                          if change['updated'] > str(one_week_ago_date):
                              fixes[user]['merged_this_week'] += 1
                          elif change['created'] > str(two_weeks_ago_date):
                              fixes[user]['merged_last_week'] += 1
                      else:
                          fixes[user]['open'] += 1
                          if change['created'] > str(one_week_ago_date):
                              fixes[user]['open_this_week'] += 1
                          elif change['created'] > str(two_weeks_ago_date):
                              fixes[user]['open_last_week'] += 1
        return fixes


if __name__ == '__main__':
    for group in engineers:
        print "\n#####################"
        print "# %s" % group
        ppl = GerritUsers(engineers[group])
        fixes = ppl.fixes(start_date, report_date, branch)


