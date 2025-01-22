from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
import asyncio


def connect_to_google_sheets(json_file, spreadsheet_name):
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
              "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
    client = gspread.authorize(creds)

    return client.open(spreadsheet_name).sheet1


work_map = {
    "language" : "cjobs_1_id",
    "math" : "djobs_2_id",
    "lab" : "djobs_3_id"
}

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
    print(normalized_time1, normalized_time2)
    return normalized_time1 == normalized_time2

def are_words_equal(word1, word2):
    return word1.strip().lower() == word2.strip().lower()

async def login_to_portal(job):
    # Initialize the Chrome browser (using Selenium Manager for driver setup)
    driver = webdriver.Chrome()
    # Load the .env file
    load_dotenv()
    USER_ID = os.getenv("USER_ID")
    PIN = os.getenv("PIN")
    ans = True
    try:
        # Navigate to the website
        driver.get("https://bweb.cbu.edu/PROD/twbkwbis.P_WWWLogin")

        # Wait for the login fields to load
        wait = WebDriverWait(driver, 10)
        user_id_field = wait.until(EC.presence_of_element_located((By.NAME, "sid")))
        pin_field = driver.find_element(By.NAME, "PIN")

        # Input User ID and PIN
        user_id_field.send_keys(USER_ID)
        pin_field.send_keys(PIN)

        # Press the login button
        login_button = driver.find_element(By.XPATH, "//input[@value='Login']")
        login_button.click()

        # Optional: Wait for the next page to load (e.g., dashboard or error message)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        employee_services_link = driver.find_element(By.LINK_TEXT, "Employee Services")
        employee_services_link.click()
        time_sheet_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Time Sheet")))
        time_sheet_link.click()
        id = work_map[job]
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))  # Wait for the page to load
        wait.until(EC.element_to_be_clickable((By.ID, id))).click()  # Use the variable 'id' to wait and click
        wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@value="Time Sheet"]'))).click()  # Wait and click the element
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))  # Wait for the page to load
        wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@alt="Clock In and Out"]'))).click()  # Wait and click
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))  # Wait for the page to load
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="Save"]'))).click()  # Wait and click
    except:
        ans = False
    finally:
        driver.quit()
        return ans


async def clock_and_update(worksheet, row_number, job,  clock_in):
    """
    Simulates clocking in for a job and updates the row in the spreadsheet.

    Args:
        worksheet (gspread.models.Worksheet): The worksheet object.
        row_number (int): The row number to update (1-indexed).

    Returns:
        None
    """
    # Fetch the row data
    ans = False
    if job != "":
        ans = await login_to_portal(job)
    row = worksheet.row_values(row_number)
    while ( len(row) < 7 ):
        row.append("")
    index = 4 if clock_in else 5
    if ans:
        row[index] =  get_current_day() + " " + get_current_date() + " " + get_current_time()  # Update 'clock in' column (index 4)
        print("clocked", "in" if clock_in else "out",  "for", row_number, job )
    else:
        row[index] = "Error"
        print("error in clocked", "in" if clock_in else "out", "for", row_number, job )
    # Update the spreadsheet row
    worksheet.update(range_name= f'A{row_number}:G{row_number}', values = [row])
    print("worksheet updated")

async def check_rows(worksheet):
    rows = worksheet.get_all_values()
    for i in range(1, len(rows)+1):
        try:
            info = get_row_info(worksheet, i)
            print(info)
            job = info.get("job", "")
            if are_words_equal(info["day"] , get_current_day()) and not are_words_equal(info.get("note", ""), "skip"):
                if are_times_equal(info["start"], get_current_time()):
                    await clock_and_update(worksheet, i, job,  True)
                elif are_times_equal(info["end"], get_current_time()):
                    await clock_and_update(worksheet, i, job, False)
        except:
            continue
    return


async def nav():
    json_file = 'creds.json'  # Path to your service account JSON file
    spreadsheet_name = 'Timesheet'  # Name of your Google Spreadsheet

    # Connect to the spreadsheet
    worksheet = connect_to_google_sheets(json_file, spreadsheet_name)
    await check_rows(worksheet)

async def wait_until_next_minute():
    now = datetime.now()
    if now.minute < 30:
        next_run = now.replace(minute=30, second=0, microsecond=0)  # Set to the next 30-minute mark
    else:
        next_run = (now + timedelta(hours=1)).replace(minute=0, second=0,
                                                      microsecond=0)  # Set to the top of the next hour
    sleep_time = (next_run - now).total_seconds()
    print(f"Sleeping for {sleep_time:.2f} seconds until {next_run}")
    await asyncio.sleep(sleep_time)  # Use asyncio.sleep for async operations



async def app():
    print("app launched")
    while True:
        await wait_until_next_minute()  # Wait for the next minute
        await nav()    # Call your async function


