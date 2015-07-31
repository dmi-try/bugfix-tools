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
    bugs = {}
    parser = argparse.ArgumentParser(description='Deploy OpenStack and run Fuel health check.')
    parser.add_argument('report_date', type=str, help="Report date.", nargs='?',
            default = datetime.datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("-l", "--login", help="Login", action="store_true")
    args = parser.parse_args()

    # Let's caclulate report dates, we need fridays since we publish bugfix report on fridays
    # but we use saturday as report_date in order to use '<' in date strings comparision.
    report_week = (datetime.datetime.strptime(args.report_date, '%Y-%m-%d') - \
            datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    one_week_ago = (datetime.datetime.strptime(args.report_date, '%Y-%m-%d') - \
            datetime.timedelta(weeks=1) - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    two_weeks_ago = (datetime.datetime.strptime(args.report_date, '%Y-%m-%d') - \
            datetime.timedelta(weeks=2) - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    print report_week
    print one_week_ago
    print two_weeks_ago

    # Login with your Google account
    gc = gspread.authorize(credentials)

    # Open worksheet from spreadsheet
    patches_sh = gc.open_by_key(SpreadsheetKey)

    # Let's gather engineers info and build patches_worksheets dict
    patches_worksheet_list = patches_sh.worksheets()
    patches_worksheets = {}
    for worksheet in patches_worksheet_list:
        if worksheet.title == 'template' or worksheet.title == 'template proposal':
            continue
        # getting list of engineers from worksheet
        patches_worksheets[worksheet.title] = []
        engineers = worksheet.col_values(1)[1:]
        patches_worksheets[worksheet.title].append(engineers)

    # Let's gather gerrit and LP info now, it can take a while
    for ws in patches_worksheets:
        for engineers in patches_worksheets[ws]:
            print "Gathering gerrit reviews info for '%s' worksheet, engineers: %s" % (ws, engineers)
            ppl = GerritUsers(engineers)
            fixes[ws] = ppl.fixes(start_date, args.report_date, branch, cachedir="/var/tmp/.gerrit")
            print "Gathering LP bugs fixed info for '%s' worksheet, engineers: %s" % (ws, engineers)
            lp_ppl = LpUsers(engineers, login = args.login)
            bugs[ws] = lp_ppl.bugs(start_date, args.report_date, ms, cachedir='/var/tmp/.launchpadlib')

    # Another login session with our Google account to avoid 502 errors due to timeouts
    second_gc = gspread.authorize(credentials)

    # Now we can update google doc
    second_sh = second_gc.open_by_key(SpreadsheetKey)
    for ws in patches_worksheets:
        # updating every worksheet
        worksheet = second_sh.worksheet(ws)
        safe_method(worksheet.update_cell, 1, 1, "Report date: %s" % report_week)
        safe_method(worksheet.update_cell, 1, 2, "Gerrit bugfixes proposed\nTotally")
        safe_method(worksheet.update_cell, 1, 3, "Gerrit bugfixes merged\nTotally")
        safe_method(worksheet.update_cell, 1, 4, "Gerrit bugfixes proposed\n%s / %s" % (one_week_ago, report_week))
        safe_method(worksheet.update_cell, 1, 5, "Gerrit bugfixes merged\n%s / %s" % (one_week_ago, report_week))
        safe_method(worksheet.update_cell, 1, 6, "Gerrit bugfixes proposed\n%s / %s" % (two_weeks_ago, one_week_ago))
        safe_method(worksheet.update_cell, 1, 7, "Gerrit bugfixes merged\n%s / %s" % (two_weeks_ago, one_week_ago))
        safe_method(worksheet.update_cell, 1, 8, 'Assigned LP bugs\nCrit/High Fixed')
        safe_method(worksheet.update_cell, 1, 9, 'Assigned LP bugs\nOther Fixed')
        for engineers in patches_worksheets[ws]:
            for engineer in engineers:
                # updating info for every engineer
                high_bugs = 0
                other_bugs = 0
                high_tricky_bugs = 0
                other_tricky_bugs = 0
                for bug in bugs[ws][engineer]:
                    if bug['importance'] in ['Critical', 'High']:
                        high_bugs += 1
                        if 'tricky' in bug['tags']:
                            high_tricky_bugs += 1
                    else:
                        other_bugs += 1
                        if 'tricky' in bug['tags']:
                            other_tricky_bugs += 1
                print "Updating worksheet info for %s" % engineer
                cell = safe_method(worksheet.find, engineer)
                safe_method(worksheet.update_cell, cell.row, cell.col + 1, len(fixes[ws][engineer]['open']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 2, len(fixes[ws][engineer]['merged']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 3, len(fixes[ws][engineer]['open_this_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 4, len(fixes[ws][engineer]['merged_this_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 5, len(fixes[ws][engineer]['open_last_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 6, len(fixes[ws][engineer]['merged_last_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 7, high_bugs)
                safe_method(worksheet.update_cell, cell.row, cell.col + 8, other_bugs)

#########################

if __name__ == '__main__':
    main()

