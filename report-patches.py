from pygerrit.rest import GerritRestAPI
import datetime
import argparse
from gerrit import GerritUsers
from oauth2client.client import SignedJwtAssertionCredentials
import gspread

start_date = '2015-06-22'
report_date = '2015-07-25'
branch = 'master'

ServiceAccountEmail = '337224127279-i9p9npr0mnuniabislf5k87r8cjjml4e@developer.gserviceaccount.com'
SpreadsheetKey = '1xx0JxeU4ySdIKckU2jyar6zplAz6RNj0jukRJkcCgOM'

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
if __name__ == '__main__':
    # Login with your Google account
    gc = gspread.authorize(credentials)

    # Open a worksheet from spreadsheet with one shot
    sh =  gc.open_by_key(SpreadsheetKey)
    worksheet_list = sh.worksheets()
    for worksheet in worksheet_list:
        if worksheet.title == 'template':
            continue
        engineers = worksheet.col_values(1)[1:]
        print "Gathering info for '%s' worksheet, engineers: %s" % (worksheet.title, engineers)
        ppl = GerritUsers(engineers)
        fixes = ppl.fixes(start_date, report_date, branch)
        for engineer in fixes:
            print "Updating worksheet info for %s" % engineer
            cell = worksheet.find(engineer)
            worksheet.update_cell(cell.row, cell.col + 1, fixes[engineer]['open'])
            worksheet.update_cell(cell.row, cell.col + 2, fixes[engineer]['merged'])
            worksheet.update_cell(cell.row, cell.col + 3, fixes[engineer]['open_this_week'])
            worksheet.update_cell(cell.row, cell.col + 4, fixes[engineer]['merged_this_week'])
            worksheet.update_cell(cell.row, cell.col + 5, fixes[engineer]['open_last_week'])
            worksheet.update_cell(cell.row, cell.col + 6, fixes[engineer]['merged_last_week'])
