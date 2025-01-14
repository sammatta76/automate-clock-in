from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def connect_to_google_sheets(json_file, spreadsheet_name):
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
              "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
    client = gspread.authorize(creds)

    return client.open(spreadsheet_name).sheet1

json_file = 'creds.json'  # Path to your service account JSON file
spreadsheet_name = 'Timesheet'  # Name of your Google Spreadsheet

# Connect to the spreadsheet
worksheet = connect_to_google_sheets(json_file, spreadsheet_name)
print("Successfully connected to the spreadsheet!")


def get_current_time():
    """
    Returns the current time in HH:MM format (24-hour clock).
    """
    return datetime.now().strftime("%H:%M")

def get_current_day():
    """
    Returns the current day of the week (e.g., "Monday", "Tuesday").
    """
    return datetime.now().strftime("%A")

def get_current_date():
    """
    Returns the current date in MM/DD/YYYY format.
    """
    return datetime.now().strftime("%m/%d/%Y")


def clock_and_update(worksheet, row_number, clock_in):
    """
    Simulates clocking in for a job and updates the row in the spreadsheet.

    Args:
        worksheet (gspread.models.Worksheet): The worksheet object.
        row_number (int): The row number to update (1-indexed).

    Returns:
        None
    """
    # Fetch the row data
    row = worksheet.row_values(row_number)
    while ( len(row) < 7 ):
        row.append("")
    index = 4 if clock_in else 5
    row[index] =  get_current_day() + " " + get_current_date() + " " + get_current_time()  # Update 'clock in' column (index 4)

    # Update the spreadsheet row
    worksheet.update(range_name= f'A{row_number}:G{row_number}', values = [row])

    print(f"Clocked in for job '{row[1]}' at {get_current_time()}")


def get_row_info(worksheet, row_number):
    row = worksheet.row_values(row_number)  # Fetch the row data
    # Map the row values to the respective keys
    keys = ['day', 'job', 'start', 'end', 'clock in', 'clock out', 'note']
    row_info = dict(zip(keys, row))
    return row_info


def print_all_rows(worksheet):
    rows = worksheet.get_all_values()  # Get all rows as a list of lists
    for row in rows:
        print(row)

def are_times_equal(time1, time2):
    """
    Compares two times in %H:%M format, ignoring leading zeroes.

    Args:
        time1 (str): The first time (e.g., '08:30').
        time2 (str): The second time (e.g., '8:30').

    Returns:
        bool: True if the times are equal, False otherwise.
    """
    # Normalize both times by parsing and reformatting
    from datetime import datetime
    format = "%H:%M"

    normalized_time1 = datetime.strptime(time1, format).strftime("%H:%M")
    normalized_time2 = datetime.strptime(time2, format).strftime("%H:%M")
    print(normalized_time1 ,  normalized_time2)
    return normalized_time1 == normalized_time2

def are_words_equal(word1, word2):
    return word1.strip().lower() == word2.strip().lower()

def check_rows(worksheet):
    rows = worksheet.get_all_values()
    for i in range(1, len(rows)+1):
        try:
            info = get_row_info(worksheet, i)
            print(info)
            if are_words_equal(info["day"] , get_current_day()) and not are_words_equal(info.get("note", ""), "skip"):
                if are_times_equal(info["start"], get_current_time()):
                    clock_and_update(worksheet, i, True)
                elif are_times_equal(info["end"], get_current_time()):
                    clock_and_update(worksheet, i, False)
        except:
            continue
    return

# info = get_row_info(worksheet, 3)
check_rows(worksheet)





