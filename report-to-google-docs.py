import datetime
import argparse
import gspread
from gerrit import GerritUsers
from lp import LpUsers
from oauth2client.client import SignedJwtAssertionCredentials

start_date = '2015-06-22'
branch = 'master'
ms = '7.0'

# Email of our google service account
ServiceAccountEmail = '337224127279-i9p9npr0mnuniabislf5k87r8cjjml4e@developer.gserviceaccount.com'
# Source of users
PatchesSpreadsheetKey = '1xx0JxeU4ySdIKckU2jyar6zplAz6RNj0jukRJkcCgOM'
# Will be updated automatically including users
BugsSpreadsheetKey = '1-2DdMePkPCJiEQnNFkkK4Gt_l9FguKBNl5iUkwktZJI'

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
    parser = argparse.ArgumentParser(description='Deploy OpenStack and run Fuel health check.')
    parser.add_argument('report_date', type=str, help="Report date.", nargs='?',
            default = datetime.datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()
    print args.report_date

    # Login with your Google account
    gc = gspread.authorize(credentials)

    # Open worksheet from spreadsheet
    patches_sh = gc.open_by_key(PatchesSpreadsheetKey)

    # Let's gather patches info and build patches_worksheets dict
    patches_worksheet_list = patches_sh.worksheets()
    patches_worksheets = {}
    for worksheet in patches_worksheet_list:
        if worksheet.title != 'bugfix-team':
            continue
        # Get list of engineers from Patches worksheet
        patches_worksheets[worksheet.title] = []
        engineers = worksheet.col_values(1)[1:]
        patches_worksheets[worksheet.title].append(engineers)

    # Let's gather herrit and LP info now, it can take a while
    for ws in patches_worksheets:
        for engineers in patches_worksheets[ws]:
            fixes = {}
            print "Gathering gerrit reviews info for '%s' worksheet, engineers: %s" % (ws, engineers)
            ppl = GerritUsers(engineers)
            fixes[ws] = ppl.fixes(start_date, args.report_date, branch)
            print "Gathering LP bugs fixed info for '%s' worksheet, engineers: %s" % (ws, engineers)
            bugs = {}
            lp_ppl = LpUsers(engineers)
            bugs[ws] = lp_ppl.bugs(start_date, args.report_date, ms, cachedir='/var/tmp/.launchpadlib')

    # Another login session with our Google account to avoid 502 errors due to timeouts
    second_gc = gspread.authorize(credentials)

    # Now we can update google doc
    second_sh = second_gc.open_by_key(PatchesSpreadsheetKey)
    for ws in patches_worksheets:
        # Now let's update patches worksheet
        worksheet = second_sh.worksheet(ws)
        safe_method(worksheet.update_cell, 1, 1, "Report date: %s" % args.report_date)
        safe_method(worksheet.update_cell, 1, 8, 'Assigned bugs fixed')
        for engineers in patches_worksheets[ws]:
            for engineer in engineers:
                print "Updating worksheet info for %s" % engineer
                cell = safe_method(worksheet.find, engineer)
                safe_method(worksheet.update_cell, cell.row, cell.col + 1, len(fixes[ws][engineer]['open']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 2, len(fixes[ws][engineer]['merged']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 3, len(fixes[ws][engineer]['open_this_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 4, len(fixes[ws][engineer]['merged_this_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 5, len(fixes[ws][engineer]['open_last_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 6, len(fixes[ws][engineer]['merged_last_week']))
                safe_method(worksheet.update_cell, cell.row, cell.col + 7, len(bugs[ws][engineer]['fixed']))

#########################

if __name__ == '__main__':
    main()

