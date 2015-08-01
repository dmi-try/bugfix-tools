import datetime
import argparse
import gspread
import sys
from gerrit import GerritUsers
from lp import LpUsers
from oauth2client.client import SignedJwtAssertionCredentials

start_date = '2015-06-22'
branch = 'master'
ms = '7.0'

# Email of our google service account
ServiceAccountEmail = '337224127279-i9p9npr0mnuniabislf5k87r8cjjml4e@developer.gserviceaccount.com'
# Source of users
SpreadsheetKey = '1xx0JxeU4ySdIKckU2jyar6zplAz6RNj0jukRJkcCgOM'

# Google service account OAuth2 credentials
credentials = SignedJwtAssertionCredentials(
    ServiceAccountEmail,
    open(".google_key.p12").read(),
    scope=(
        'https://www.googleapis.com/auth/drive.file',
        'https://spreadsheets.google.com/feeds',
        'https://docs.google.com/feeds'
    ),
)

#########################
def safe_method(method, *args):
    for i in range(0,10):
        try:
            return method(*args)
        except:
            pass

def main():
    fixes = {}
    bugs_cur = {}
    bugs_last = {}
    parser = argparse.ArgumentParser(description='Deploy OpenStack and run Fuel health check.')
    parser.add_argument('report_date', type=str, help="Report date.", nargs='?',
            default = datetime.datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("-l", "--login", help="Login", action="store_true")
    args = parser.parse_args()

    # Let's caclulate report dates, we need fridays since we publish bugfix report on fridays
    # but we use saturday as report_date in order to use '<' in date strings comparision.
    report_day = datetime.datetime.strptime(args.report_date, '%Y-%m-%d')
    last_sun = report_day - datetime.timedelta(days=report_day.weekday()) + \
            datetime.timedelta(days=6, weeks=-1)
    prelast_sun = last_sun - datetime.timedelta(weeks=1)
    last_mon = last_sun + datetime.timedelta(days=1)
    print "Report day: %s" % report_day
    print "Last Monday: %s" % last_mon
    print "Last Sunday: %s" % last_sun
    print "Pre-last Sunday: %s" % prelast_sun

    # Login with your Google account
    gc = gspread.authorize(credentials)

    # Open worksheet from spreadsheet
    patches_sh = gc.open_by_key(SpreadsheetKey)

    # Let's gather engineers info and build patches_worksheets dict
    patches_worksheet_list = patches_sh.worksheets()
    patches_worksheets = {}
    for worksheet in patches_worksheet_list:
        if worksheet.title == 'template':
            continue
        # getting list of engineers from worksheet
        patches_worksheets[worksheet.title] = []
        engineers = worksheet.col_values(1)[2:-2]
        patches_worksheets[worksheet.title].append(engineers)

    # Let's gather gerrit and LP info now, it can take a while
    for ws in patches_worksheets:
        for engineers in patches_worksheets[ws]:
            print "Gathering gerrit reviews info for '%s' worksheet, engineers: %s" % (ws, engineers)
            ppl = GerritUsers(engineers)
            fixes[ws] = ppl.fixes(start_date, report_day.strftime('%Y-%m-%d'), branch, cachedir="/var/tmp/.gerrit")
            print "Gathering LP bugs fixed info for '%s' worksheet, engineers: %s" % (ws, engineers)
            lp_ppl = LpUsers(engineers, login = args.login)
            # Get info from start to last Sun and cache it for future
            bugs_last[ws] = lp_ppl.bugs(start_date, last_mon.strftime('%Y-%m-%d'), ms, cachedir='/var/tmp/.launchpadlib')
            # Get info for current week and cache it separately
            bugs_cur[ws] = lp_ppl.bugs(last_sun.strftime('%Y-%m-%d'), report_day.strftime('%Y-%m-%d'), ms, cachedir='/var/tmp/.curlaunchpadlib')

    # Another login session with our Google account to avoid 502 errors due to timeouts
    second_gc = gspread.authorize(credentials)

    # Now we can update google doc
    second_sh = second_gc.open_by_key(SpreadsheetKey)
    for ws in patches_worksheets:
        # updating every worksheet
        worksheet = second_sh.worksheet(ws)
        safe_method(worksheet.update_cell, 1, 1, "Report date: %s" % report_day.strftime('%Y-%m-%d'))
        for engineers in patches_worksheets[ws]:
            for engineer in engineers:
                # updating info for every engineer
                # calculating bugs
                current_week_bugs = []
                last_week_bugs = []
                inprogress_bugs = []
                total_bugs = []
                for bug in bugs_last[ws][engineer] + bugs_cur[ws][engineer]:
                    print "%s %s %s %s" % (bug['web_link'], bug['importance'], bug['status'], bug['change_date'])
                    if bug['importance'] in ['Critical', 'High']:
                        if bug['change_date'][:10] >= last_sun.strftime('%Y-%m-%d'):
                            if bug['status'] in ["Fix Committed", "Fix Released"]:
                                total_bugs.append(bug['web_link'])
                                current_week_bugs.append(bug['web_link'])
                            elif bug['status'] == "In Progress":
                                inprogress_bugs.append(bug['web_link'])
                        elif bug['change_date'][:10] >= prelast_sun.strftime('%Y-%m-%d'):
                            if bug['status'] in ["Fix Committed", "Fix Released"]:
                                total_bugs.append(bug['web_link'])
                                last_week_bugs.append(bug['web_link'])
                        else:
                            total_bugs.append(bug['web_link'])

                print "Updating worksheet info for %s" % engineer
                cell = safe_method(worksheet.find, engineer)
                safe_method(worksheet.update_cell, cell.row, cell.col + 1, len(fixes[ws][engineer]['open_this_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 2, len(fixes[ws][engineer]['merged_this_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 3, len(inprogress_bugs))
                safe_method(worksheet.update_cell, cell.row, cell.col + 4, len(current_week_bugs))
                safe_method(worksheet.update_cell, cell.row, cell.col + 5, len(fixes[ws][engineer]['merged_last_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 6, len(last_week_bugs))
                safe_method(worksheet.update_cell, cell.row, cell.col + 7, len(fixes[ws][engineer]['merged']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 8, len(total_bugs))

#########################

if __name__ == '__main__':
    main()

