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
    # which will be used in LP doc later
    patches_worksheet_list = patches_sh.worksheets()
    patches_worksheets = {}
    for worksheet in patches_worksheet_list:
        if worksheet.title == 'template':
            continue
        # Get list of engineers from Patches worksheet
        patches_worksheets[worksheet.title] = []
        engineers = worksheet.col_values(1)[1:]
        patches_worksheets[worksheet.title].append(engineers)
        print "Gathering gerrit reviews info for '%s' worksheet, engineers: %s" % (worksheet.title, engineers)
        ppl = GerritUsers(engineers)
        fixes = ppl.fixes(start_date, args.report_date, branch)
        # Now let's update worksheets
        worksheet.update_cell(1, 1, "Report date: %s" % args.report_date)
        for engineer in fixes:
            print "Updating worksheet info for %s" % engineer
            cell = worksheet.find(engineer)
            worksheet.update_cell(cell.row, cell.col + 1, len(fixes[engineer]['open']))
            worksheet.update_cell(cell.row, cell.col + 2, len(fixes[engineer]['merged']))
            worksheet.update_cell(cell.row, cell.col + 3, len(fixes[engineer]['open_this_week']))
            worksheet.update_cell(cell.row, cell.col + 4, len(fixes[engineer]['merged_this_week']))
            worksheet.update_cell(cell.row, cell.col + 5, len(fixes[engineer]['open_last_week']))
            worksheet.update_cell(cell.row, cell.col + 6, len(fixes[engineer]['merged_last_week']))

    # Let's gather LP info now, it can take a while
    for worksheet in patches_worksheets:
        for engineers in patches_worksheets[worksheet]:
            print "Gathering LP bugs fixed info for '%s' worksheet, engineers: %s" % (worksheet, engineers)
            bugs = {}
            lp_ppl = LpUsers(engineers)
            bugs[worksheet] = lp_ppl.bugs(start_date, args.report_date, ms, cachedir='/var/tmp/.launchpadlib')

    # Another login session with our Google account to avoid 502 errors due to timeouts
    bug_gc = gspread.authorize(credentials)

    # Now we can update LP google doc in a separate loop to avoid google doc timeouts
    bugs_sh = bug_gc.open_by_key(BugsSpreadsheetKey)
    for worksheet in patches_worksheets:
        print "Going to update %s spreadsheet in Google LP doc" % worksheet
        # Let's check LP bugs ws and create it if it's missing
        try:
            bugs_worksheet = bugs_sh.worksheet(worksheet)
        except:
            bugs_worksheet = bugs_sh.add_worksheet(title=worksheet, rows="100", cols="20")
        bugs_worksheet.update_cell(1, 1, "Report date: %s" % args.report_date)
        for engineer in bugs[worksheet]:
            print "Updating worksheet info for %s" % engineer
            cell = bugs_worksheet.find(engineer)
            bugs_worksheet.update_cell(1, cell.col + 1, 'Assigned bugs fixed')
            bugs_worksheet.update_cell(cell.row, cell.col + 1, len(bugs[worksheet][engineer]['fixed']))

#########################

if __name__ == '__main__':
    main()

