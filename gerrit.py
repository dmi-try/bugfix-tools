from pygerrit.rest import GerritRestAPI
import datetime
import pickle

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
    def __init__(self, users, url = 'https://review.openstack.org'):
        self.users = users
        self.rest = GerritRestAPI(url=url)

    def fixes(self, start_date, report_date, branch, cachedir = "~/.gerrit"):
        fixes = {}
        report_day = datetime.datetime.strptime(report_date, '%Y-%m-%d')
        last_sun = report_day - datetime.timedelta(days=report_day.weekday()) + \
                datetime.timedelta(days=6, weeks=-1)
        prelast_sun = last_sun - datetime.timedelta(weeks=1)

        projects = ['^stackforge/fuel-.*', '^stackforge/python-fuel.*']
        template = '/changes/?q=project:%s+owner:".*<%s@mirantis.com>"+message:"bug:+"'
        url = 'https://review.openstack.org/#/c/%s'

        for user in self.users:
            fixes[user] = {}
            fixes[user]['merged'] = []
            fixes[user]['merged_this_week'] = []
            fixes[user]['merged_last_week'] = []
            fixes[user]['open_this_week'] = []
            # Let's use something like cache to no overload gerrit API and improve performance
            cache_filename = "%s/%s_%s_%s_%s.grc" % (cachedir, user, report_date, start_date, branch)
            try:
                cache_file = open(cache_filename, 'rb')
                fixes[user] = pickle.load(cache_file)
                cache_file.close()
                continue
            except:
                pass

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
                            if change['updated'][:10] > str(last_sun)[:10]:
                                fixes[user]['merged_this_week'].append(url % change['_number'])
                            elif change['created'][:10] > str(prelast_sun)[:10]:
                                fixes[user]['merged_last_week'].append(url % change['_number'])
                        else:
                            if change['created'][:10] > str(last_sun)[:10]:
                                fixes[user]['open_this_week'].append(url % change['_number'])

            # Let's use something like cache to no overload gerrit API and improve performance
            try:
                cache_file = open(cache_filename, 'wb')
                pickle.dump(fixes[user], cache_file)
                cache_file.close()
            except:
                pass

        return fixes

if __name__ == '__main__':
    for group in engineers:
        print "\n#####################"
        print "# %s" % group
        ppl = GerritUsers(engineers[group])
        fixes = ppl.fixes(start_date, report_date, branch)

