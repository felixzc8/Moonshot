import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time
import json
import csv
import pandas as pd
from helpers.parser_helpers import parse_search_timeline_response
import random
# from accounts_cookies import cookies
import datetime
from datetime import datetime, timezone
import multiprocessing
import os
import importlib.util

from bs4 import BeautifulSoup
import requests
import time

OUTPUT_FILENAME = "parsed_tweets/testingTwoAccountRotation"
CREDENTIAL_FILENAME = "accounts.temp.json"
COOKIE_FILENAME = "accounts_cookies.temp.json"
PARAMETERS_FILENAME = "parameters.json"
ERROR_FILE = "error.txt"

def stop_there():
    try:
        input("Press Enter to exit...\n")
    except KeyboardInterrupt:
        pass

def get_required_time_data(epoch):
    # dt = datetime.datetime.utcfromtimestamp(epoch)
    dt = datetime.fromtimestamp(epoch)
    year = dt.year
    month = dt.month
    day = dt.day
    formatted_month = dt.strftime('%-m')
    formatted_day = dt.strftime('%-d')

    return {"month":formatted_month, "day":formatted_day, "year":str(year)}

def append_csv_to_file(filename, data):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

def append_csv_to_file_after_pre_processing(file_path, new_data):
    if len(new_data) == 0:
        return
    try:
        existing_data = pd.read_csv(file_path)
    except FileNotFoundError:
        existing_data = pd.DataFrame(columns=new_data[0].keys())
    new_data_df = pd.DataFrame(new_data)
    updated_data = pd.concat([existing_data, new_data_df], ignore_index=True)
    updated_data.to_csv(file_path, index=False)
    print(f"Number of tweets currently present in the file: {len(updated_data)}")

def keep_scrolling(page, count):
    while count >= 0:
        page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
        count -= 1
        time.sleep(random.randint(1, 18))

def get_date_obj_from_epoch(epoch):
    # Convert the epoch timestamp to a datetime object in UTC
    utc_datetime = datetime.fromtimestamp(epoch, timezone.utc)

    # Create the startDate dictionary
    date_obj = {
        "year": utc_datetime.year,
        "month": utc_datetime.month,
        "day": utc_datetime.day,
        "hours": utc_datetime.hour,
        "mins": utc_datetime.minute,
        "secs": utc_datetime.second
    }

    return date_obj

def run(playwright: Playwright, cookies, search_string, parameter_data, outputfile) -> None:
    rate_limit_reset_epoch_time = None
    remaining_count = 50
    total_tweets_of_this_session = 0
    max_tweets_of_this_session = 4300 + random.randint(4, 600)
    epoch_of_last_added_tweet = None
    number_of_tweets = 0

    def intercept_response(response):
        nonlocal remaining_count, rate_limit_reset_epoch_time, total_tweets_of_this_session, epoch_of_last_added_tweet
        if response.request.resource_type == "xhr" and "SearchTimeline" in response.request.url:
            data = response.json()
            remaining_count = int(response.headers.get("x-rate-limit-remaining"))
            rate_limit_reset_epoch_time = int(response.headers.get("x-rate-limit-reset"))
            result = parse_search_timeline_response(data['data']['search_by_raw_query'])
            if result["tweet_count"] > 0:
                total_tweets_of_this_session += int(result["tweet_count"])
                epoch_of_last_added_tweet = int(result["last_tweet_epoch"])
                append_csv_to_file_after_pre_processing(outputfile, result["data"])
                print(f"Last added tweet epoch: {epoch_of_last_added_tweet}")
        return response

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        viewport={'width': 1280, 'height': 800},
        java_script_enabled=True,
        locale='en-US'
    )
    context.add_cookies(cookies)
    page = context.new_page()
    page.goto("https://x.com/")
    # page.get_by_test_id("xMigrationBottomBar").click()
    page.get_by_test_id("SearchBox_Search_Input").click()
    page.get_by_test_id("SearchBox_Search_Input").fill(search_string)
    page.get_by_test_id("SearchBox_Search_Input").press("Enter")
    time.sleep(60)
    page.get_by_role("tab", name="Latest").click()
    page.on("response", intercept_response)
    time.sleep(5)
    keep_scrolling(page, 3)
    while True:
        print("\n")
        print(f"Rate limit reset after: {rate_limit_reset_epoch_time}")
        print(f"Remaining count of available requests for this rate limit period: {remaining_count}")
        print(f"Total tweets of this session: {total_tweets_of_this_session} {outputfile}")
        print(f"Max tweets of this session: {max_tweets_of_this_session}")
        current_epoch_time = int(time.time())
        try:
            if total_tweets_of_this_session >= max_tweets_of_this_session:
                break
            if rate_limit_reset_epoch_time is not None and rate_limit_reset_epoch_time <= current_epoch_time:
                print(f"ERROR: current_epoch time is greater than rate limit epoch time {outputfile}")
                try:
                    element = page.locator('[data-testid="empty_state_body_text"]')
                    if element.is_visible():
                        epoch_of_last_added_tweet -= (60 * 60)
                        print("MODIFIED THE EPOCH", epoch_of_last_added_tweet)
                except Exception as e:
                    print(f"Element not found: {e}")
                new_end_date = get_date_obj_from_epoch(epoch_of_last_added_tweet)
                new_search_string = get_search_string(parameter_data, new_end_date)
                page.get_by_test_id("SearchBox_Search_Input").click()
                page.get_by_test_id("SearchBox_Search_Input").fill(new_search_string)
                print("NEW _____ SEARCH ___ STRING ____", new_search_string)
                page.get_by_test_id("SearchBox_Search_Input").press("Enter")
                time.sleep(3)
                keep_scrolling(page, 3)
            elif remaining_count <= random.randint(9, 15):
                seconds_to_wait = rate_limit_reset_epoch_time - current_epoch_time
                seconds_to_wait += random.randint(1, 53)
                print(f"Will sleep until: {current_epoch_time + seconds_to_wait}")
                time.sleep(seconds_to_wait)
                keep_scrolling(page, 2)
                print(f"Updated: rate limit reset epoch time and remaining count after sleep: {rate_limit_reset_epoch_time} & {remaining_count}")
            else:
                keep_scrolling(page, 1)
        except Exception as e:
            with open(ERROR_FILE, 'a') as f:
                f.write("**************************\n")
                f.write(str(e) + '\n')
                f.write(f"last_tweet_epoch: {epoch_of_last_added_tweet}\n")
    context.close()
    browser.close()
    return epoch_of_last_added_tweet

def relogin_to_update_cookies(credentials_file, output_file):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        with open(credentials_file, 'r') as f:
            data = pd.read_csv(f)
        all_cookies = {'cookies': []}
        for _, account in data.iterrows():
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://x.com/")
            page.get_by_test_id("loginButton").click()
            page.locator("label div").nth(3).click()
            page.get_by_label("Phone, email address, or").fill(account["email"])
            page.get_by_role("button", name="Next").click()
            page.get_by_label("Password", exact=True).fill(account["password"])
            page.get_by_test_id("LoginForm_Login_Button").click()
            page.get_by_test_id("SearchBox_Search_Input").fill("US Elections")
            page.get_by_test_id("SearchBox_Search_Input").press("Enter")
            page.wait_for_load_state('networkidle')
            cookies = context.cookies()
            all_cookies['cookies'].append(cookies)
            context.close()
        with open(output_file, 'w') as f:
            json.dump(all_cookies, f, indent=4)
        browser.close()

def get_epoch_time(data):
    # Extract the date information
    year = int(data["year"])
    month = int(data["month"])
    day = int(data["day"])

    # Create a datetime object
    date_obj = datetime.datetime(year, month, day)

    # Convert the datetime object to epoch time
    epoch_time = int(date_obj.timestamp())
    return epoch_time

def get_search_string(parameter_data, end_date):
    if parameter_data["mode"] == "ANY":
        keywords_string = " OR ".join(parameter_data["keywords"])
        start_date = parameter_data["startDate"]
        start_date_string = f'since:{start_date["year"]}-{start_date["month"]:02d}-{start_date["day"]:02d}_{start_date["hours"]:02d}:{start_date["mins"]:02d}:{start_date["secs"]:02d}_UTC'
        end_date_string = f'until:{end_date["year"]}-{end_date["month"]:02d}-{end_date["day"]:02d}_{end_date["hours"]:02d}:{end_date["mins"]:02d}:{start_date["secs"]:02d}_UTC'
        final_string = f'({keywords_string}) {end_date_string} {start_date_string} '
        return final_string
    elif parameter_data["mode"] == "EXACT":
        keywords_string =' OR '.join([f'"{keyword}"' for keyword in parameter_data["keywords"]])
        start_date = parameter_data["startDate"]
        start_date_string = f'since:{start_date["year"]}-{start_date["month"]:02d}-{start_date["day"]:02d}_{start_date["hours"]:02d}:{start_date["mins"]:02d}:{start_date["secs"]:02d}_UTC'
        end_date_string = f'until:{end_date["year"]}-{end_date["month"]:02d}-{end_date["day"]:02d}_{end_date["hours"]:02d}:{end_date["mins"]:02d}:{start_date["secs"]:02d}_UTC'
        final_string = f'({keywords_string}) {end_date_string} {start_date_string} '
        return final_string

def get_last_entry_epoch_csv(file_name):
    try:
        # Read the CSV file
        df = pd.read_csv(file_name, low_memory=False)
        
        if df.empty:
            print("The CSV file is empty.")
            return None
        
        if 'epoch' not in df.columns:
            print("CSV data does not contain an 'epoch' column.")
            return None
        
        # Get the last row in the DataFrame
        last_entry = df.iloc[-1]
        
        # Retrieve the 'epoch' value
        epoch_value = last_entry['epoch']
        print("Epoch Value:", epoch_value)
        return epoch_value

    except FileNotFoundError:
        print(f"Error: The file '{file_name}' was not found.")
    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty or only contains headers.")
    except pd.errors.ParserError as pe:
        print(f"Error: The file could not be parsed as CSV. {pe}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
def is_csv_not_empty(file_path):
    try:
        df = pd.read_csv(file_path, low_memory=False)
        return not df.empty
    except FileNotFoundError:
        print("File not found.")
        return False
    
def current_file_part(filename):
    part = 1
    while os.path.exists(f"{filename}part{part}.csv"):
        part += 1
    return part

def next_file_name(filename):
    current = current_file_part(filename)
    return (f"{filename}part{current}.csv")

def number_of_entries(filename):
    currentTweets = pd.read_csv(filename)
    return len(currentTweets)

def main(outputfile, parametersfile, cookies_module):
    last_tweet_epoch = None
    parameter_data = None

    with open(parametersfile) as f:
        parameter_data = json.load(f)
    
    if is_csv_not_empty(outputfile):
        last_tweet_epoch = get_last_entry_epoch_csv(outputfile)
        end_date = get_date_obj_from_epoch(last_tweet_epoch)
    else:
        end_date = parameter_data["endDate"]

    # Define stopping conditions
    max_attempts = 3  # Stop if no new tweets after 3 retries
    max_wait_time = 5 * 60  # Stop if rate limit forces wait over **5 minutes**
    no_new_tweet_attempts = 0  # Counter for failed scraping attempts

    while True:
        list_accounts = [x for x in range(0, len(cookies_module.cookies))]

        while len(list_accounts) != 0:
            index = random.randint(0, len(list_accounts) - 1)
            print(f"Current Account Index: {list_accounts[index]}")

            with sync_playwright() as playwright:
                search_string = get_search_string(parameter_data, end_date)
                print("SEARCH STRING:", search_string)
                try:
                    # Run the scraper
                    new_last_tweet_epoch = run(playwright, cookies_module.cookies[list_accounts[index]], search_string, parameter_data, outputfile)

                    # Check if a new tweet was found
                    if new_last_tweet_epoch == last_tweet_epoch or new_last_tweet_epoch is None:
                        no_new_tweet_attempts += 1
                        print(f"No new tweets found. Attempt {no_new_tweet_attempts}/{max_attempts}")
                    else:
                        no_new_tweet_attempts = 0  # Reset counter
                        last_tweet_epoch = new_last_tweet_epoch  # Update epoch

                except Exception as e:
                    print(f"Error: {str(e)}")
                    with open(ERROR_FILE, "a") as f:
                        f.write("**************************\n")
                        f.write(str(e) + '\n')
                        f.write(f"Last Tweet Epoch: {last_tweet_epoch}\n")

            # **Check stopping conditions**
            if no_new_tweet_attempts >= max_attempts:
                print("Stopping: No new tweets found after 3 attempts.")
                return  # Exit function safely

            if last_tweet_epoch is None:
                print("Stopping: No tweets found at all. Exiting.")
                return  # No tweets = exit early

            # Update scraping date
            end_date = get_date_obj_from_epoch(last_tweet_epoch)
            print(f"Next Date Object: {str(end_date)}")

            # **Cooldown timer (shorter due to short scraping time)**
            cooldown = random.randint(5, 30)  # **Reduced cooldown to 5-30 seconds**
            print(f"Cooling down for {cooldown} seconds...")
            time.sleep(cooldown)

            del list_accounts[index]
            print(f"Remaining accounts: {len(list_accounts)}")

# for dynamically importing the account cookies files
def dynamic_import(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def process_main(outputfile, parametersfile, cookiesfile):
    cookies_module = dynamic_import('cookies', cookiesfile)
    main(outputfile, parametersfile, cookies_module)
    
    
# Dynamic import for the cookies file
def dynamic_import_cookies(variable_name, module_path):
    spec = importlib.util.spec_from_file_location(variable_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, variable_name)

# Flatten the nested cookies list
def flatten_cookies(nested_cookies):
    if isinstance(nested_cookies, list) and all(isinstance(item, list) for item in nested_cookies):
        return [cookie for sublist in nested_cookies for cookie in sublist]
    return nested_cookies  # Return as-is if already flat
    
def extractTrending(cookiesfile):
    # cookies = dynamic_import('cookies', cookiesfile)
    
    nested_cookies = dynamic_import_cookies('cookies', cookiesfile)
    cookies = flatten_cookies(nested_cookies)  # Flatten the cookies list if needed

    
    # Debug: Print cookies
    print(f"Loaded cookies: {cookies}")
    
    with sync_playwright() as playwright:
        print("Launching Playwright...")
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            java_script_enabled=True,
            locale='en-US'
        )
        
        # Add cookies
        print("Adding cookies...")
        context.add_cookies(cookies)  # Pass the flattened cookies list
        print("Cookies added successfully.")
        
        # Navigate to trending page
        page = context.new_page()
        print("Opening Twitter/X trending page...")
        page.goto("https://x.com/explore/tabs/trending", timeout=30000)
        page.wait_for_selector('[data-testid="cellInnerDiv"]', timeout=10000)

        # Initialize trending_topics as a set
        trending_topics = set()

        # Extract initial trending topics
        print("Extracting initial trending topics...")
        trending_topics.update(page.locator('[data-testid="cellInnerDiv"]').all_inner_texts())

        # Scroll and extract additional topics
        keep_scrolling(page, 2)  # Scroll down 2 times
        page.wait_for_selector('[data-testid="cellInnerDiv"]', timeout=10000)
        print("Extracting more trending topics...")
        trending_topics.update(page.locator('[data-testid="cellInnerDiv"]').all_inner_texts())

        browser.close()
        return trending_topics
    
    return trending_topics

# print(f"{extractTrending("accounts_cookies/accounts_cookies1.py")}")
# print(os.path.exists('accounts_cookies/accounts_cookies1.py'))
# print(os.listdir('accounts_cookies'))

# if __name__ == "__main__":
    
#     filenames = [
#     ["parsed_tweets/jun10tojun11.csv", "parametersJune/parameters1.json", "accounts_cookies/accounts_cookies3.py"],
#     ]

#     with multiprocessing.Pool(processes=34) as pool:
#         pool.starmap(process_main, filenames)