#!/usr/bin/env python
import datetime
import argparse
import gspread
import sys
import pytz
from gerrit import GerritUsers
from lp import LpUsers
from oauth2client.client import SignedJwtAssertionCredentials
from itertools import groupby

# Email of our google service account
ServiceAccountEmail = '337224127279-i9p9npr0mnuniabislf5k87r8cjjml4e@developer.gserviceaccount.com'
# KPI Spreadsheet key
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

#########################
def main():
    fixes = {}
    os_fixes = {}
    infra_fixes = {}
    bugs = {}
    parser = argparse.ArgumentParser(description='Deploy OpenStack and run Fuel health check.')
    parser.add_argument('report_date', type=str, help="Report date (UTC).", nargs='?',
            default = "current")
    parser.add_argument('--start-date', type=str, help="Report start date.",
            default = "2015-06-22")
    parser.add_argument('--milestone', type=str, help="Milestone.",
            default = "7.0")
    parser.add_argument("-l", "--login", help="Login", action="store_true")
    args = parser.parse_args()

    # Let's caclulate report dates
    weekday = datetime.datetime.today().weekday()
    if args.report_date == "current":
        report_date = datetime.datetime.now(pytz.utc)
    else:
        report_date = datetime.datetime.strptime(args.report_date, '%Y-%m-%d').replace(tzinfo=pytz.utc)

    start_date = pytz.utc.localize(datetime.datetime.strptime(args.start_date, '%Y-%m-%d'))
    last_sun = report_date.replace(hour=0, minute=0, second=0, microsecond=0) - \
            datetime.timedelta(days=report_date.weekday()) + \
            datetime.timedelta(days=6, weeks=-1)
    prelast_sun = last_sun - datetime.timedelta(weeks=1)
    last_mon = last_sun + datetime.timedelta(days=1)
    print "Report date: %s" % report_date
    print "Last Monday: %s" % last_mon
    print "Last Sunday: %s" % last_sun
    print "Pre-last Sunday: %s" % prelast_sun
    ms = args.milestone
    # Login with your Google account
    gc = gspread.authorize(credentials)

    # Open worksheet from spreadsheet
    patches_sh = gc.open_by_key(SpreadsheetKey)

    # Let's gather engineers info and build patches_worksheets dict
    patches_worksheet_list = patches_sh.worksheets()
    patches_worksheets = {}
    for worksheet in patches_worksheet_list:
        if worksheet.title in ['summary', 'template']:
#        if worksheet.title != 'template':
            continue
        # getting list of engineers from worksheet
        patches_worksheets[worksheet.title] = []
        engineers = [list(group) for k, group in groupby(worksheet.col_values(1)[2:], lambda x: x == "Total") if not k]
        patches_worksheets[worksheet.title].append(engineers[0])

    # Let's gather gerrit and LP info now, it can take some time
    for ws in patches_worksheets:
        for engineers in patches_worksheets[ws]:
            print "Gathering gerrit reviews info for '%s' worksheet, engineers: %s" % (ws, engineers)
            ppl = GerritUsers(engineers)
            os_fixes[ws] = ppl.fixes(start_date, report_date, branch='master')
            ppl = GerritUsers(engineers,
                    gerrit = 'https://review.fuel-infra.org',
                    projects = ['^.*'],
                    url = 'https://review.fuel-infra.org/#/c/%s')
            infra_fixes[ws] = ppl.fixes(start_date, report_date, branch='.*')
            print "Gathering LP bugs fixed info for '%s' worksheet, engineers: %s" % (ws, engineers)
            lp_ppl = LpUsers(engineers, login = args.login)
            bugs[ws] = lp_ppl.bugs(start_date, report_date, ms)

    # Another login session with our Google account to avoid 502 errors due to timeouts
    second_gc = gspread.authorize(credentials)

    # Now we can update google doc
    second_sh = second_gc.open_by_key(SpreadsheetKey)
    for ws in patches_worksheets:
        # updating every worksheet
        worksheet = second_sh.worksheet(ws)
        safe_method(worksheet.update_cell, 1, 1, "Updated on: %s UTC" % report_date.strftime("%Y-%m-%d %H:%M"))
        for engineers in patches_worksheets[ws]:
            for engineer in engineers:
                # Updating info for every engineer
                # Calculating bugs
                current_week_bugs = []
                last_week_bugs = []
                inprogress_bugs = []
                total_bugs = []
                unresolved_bugs = []
                print "\nChecking bugs for %s" % engineer
                for bug in bugs[ws][engineer]:
                    print "%s [%s] [%s] %s" % (bug['web_link'], bug['importance'], bug['status'], bug['change_date'])
                    if bug['status'] in ["Fix Committed", "Fix Released"]:
                        if bug['change_date'] >= last_mon:
                            current_week_bugs.append(bug['web_link'])
                        elif bug['change_date'] >= prelast_sun:
                            last_week_bugs.append(bug['web_link'])
                        total_bugs.append(bug['web_link'])
                    elif bug['status'] == "In Progress":
                        inprogress_bugs.append(bug['web_link'])
                    elif bug['status'] in ["New", "Confirmed", "Triaged"]:
                        unresolved_bugs.append(bug['web_link'])

                # Calculating reviews
                fixes['open_this_week'] = os_fixes[ws][engineer]['open_this_week'] + \
                        infra_fixes[ws][engineer]['open_this_week']
                fixes['merged_this_week'] = os_fixes[ws][engineer]['merged_this_week'] + \
                        infra_fixes[ws][engineer]['merged_this_week']
                fixes['merged_last_week'] = os_fixes[ws][engineer]['merged_last_week'] + \
                        infra_fixes[ws][engineer]['merged_last_week']
                fixes['merged'] = os_fixes[ws][engineer]['merged'] + \
                        infra_fixes[ws][engineer]['merged']

                # Printing some info for debug/troubleshooting
                # TODO: re-do all the printing via logger
                print "\nUpdating worksheet info for %s" % engineer
                print "Bugs this week: %s" % current_week_bugs
                print "Bugs last week: %s" % last_week_bugs
                print "Bugs total: %s" % total_bugs
                print "Reviews open_this_week: %s" % fixes['open_this_week']
                print "Reviews merged_this_week: %s" % fixes['merged_this_week']
                print "Reviews merged_last_week: %s" % fixes['merged_last_week']
                print "Reviews merged total: %s" % fixes['merged']

                # Updating worksheet for engineer
                cell = safe_method(worksheet.find, engineer)
                cell_list = safe_method(worksheet.range, 'A%s:L%s' % (cell.row, cell.row))

                # Copy allocation to the last week on Mondays
                if weekday == 0:
                    cell_list[5].value = cell_list[1].value

                cell_list[2].value = len(fixes['open_this_week'])
                cell_list[3].value = len(fixes['merged_this_week'])
                cell_list[4].value = len(current_week_bugs)
                cell_list[6].value = len(fixes['merged_last_week'])
                cell_list[7].value = len(last_week_bugs)
                cell_list[8].value = len(unresolved_bugs)
                cell_list[9].value = len(inprogress_bugs)
                cell_list[10].value = len(fixes['merged'])
                cell_list[11].value = len(total_bugs)

                # Update cells in batch
                safe_method(worksheet.update_cells, cell_list)

    print "Finished at: %s" % datetime.datetime.now(pytz.utc)

#########################

if __name__ == '__main__':
    main()

