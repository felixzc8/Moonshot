# from backend.scraper_raw import process_main
# from backend.scraper_raw import extractTrending
from datetime import datetime, timedelta, timezone
import re
import os
import json
import multiprocessing
import shutil
import time
from pymongo import MongoClient
from app.models.tweets import Tweet
import pandas as pd
from typing import List, Optional
from scraper_raw import process_main
from scraper_raw import extractTrending
from app.config import MONGODB_URI, DB_NAME

CURRENTCOOKIE = "accounts_cookies/accounts_cookies1.py"
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
'''
accounts = n
time frame = past 6 hours
choose off trending:
    if every memecoin is around 5k tweets, and there are 2 new ones per hour, it would be around 10k tweets
    10k tweets => around 15 minutes
    4 : 1 ratio
    maybe we refresh every 15 minutes, then we scrape for 3.75 minutes every time

# Make a function that looks at the past three hours and splits
'''

def extract_trending_name(topic):
    """Extracts the text between 'Trending\n' and the next '\n'."""
    match = re.search(r'Trending\n(.*?)\n', topic)
    return match.group(1) if match else None

def getTrendingKeywords(cookiesfile) -> list:
    """Extracts trending topics related to business and finance and has $ in its name"""
    rawTopics = extractTrending(cookiesfile)

    extracted_topics = [extract_trending_name(topic) for topic in rawTopics if extract_trending_name(topic)]

    filtered_topics = [
        topic for topic in extracted_topics
        if "business and finance" in topic.lower() or topic.startswith("$")
    ]
    
    return filtered_topics
'''
Scrapes for the past minutesToScrape with numberOfAccounts

First calls getTrendingKeywords()
Then find current time and the past time using minutesToScrape in UTC
Splits the past minutesToScrape into numberOfAccounts parts, making a temporary parameters.json
'''
def splitIntoParts(numberOfAccounts: int, minutesToScrape: int):
    now = datetime.utcnow()
    past_time = now - timedelta(minutes=minutesToScrape)
    
    time_splits = [
        (past_time + timedelta(minutes=(i * minutesToScrape // numberOfAccounts)), 
         past_time + timedelta(minutes=((i + 1) * minutesToScrape // numberOfAccounts)))
        for i in range(numberOfAccounts)
    ]

    parameters_list = []
    keywords = getTrendingKeywords(CURRENTCOOKIE)
    
    for start, end in time_splits:
        params = {
            "keywords": keywords,
            "startDate": {
                "month": start.month,
                "day": start.day,
                "year": start.year,
                "hours": start.hour,
                "mins": start.minute,
                "secs": 0
            },
            "endDate": {
                "month": end.month,
                "day": end.day,
                "year": end.year,
                "hours": end.hour,
                "mins": end.minute,
                "secs": 0
            },
            "mode": "EXACT"
        }
        parameters_list.append(params)

    return parameters_list

def uploadCSV(file_path: str) -> List[Tweet]:
    df = pd.read_csv(file_path)
    tweets = []
    
    for _, row in df.iterrows():
        try:
            # tweet = Tweet(
            #     tweet_id=str(row["id_str"]),
            #     username=row["username"],
            #     tweet_body=row["rawContent"],
            #     url=row["url"],
            #     timestamp=datetime.fromtimestamp(row["epoch"], tz=timezone.utc),
            #     language=row["lang"],
            #     reply_count=row["replyCount"],
            #     retweet_count=row["retweetCount"],
            #     like_count=row["likeCount"],
            #     quote_count=row["quoteCount"],
            #     # view_count=row.get("viewCount", 0)
            #     view_count=0
            # )
            tweet = {
                "tweet_id": str(row["id_str"]),
                "username": row["username"],
                "tweet_body": row["rawContent"],
                "url": row["url"],
                "timestamp": datetime.fromtimestamp(row["epoch"], tz=timezone.utc),
                "language": row["lang"],
                "reply_count": row["replyCount"],
                "retweet_count": row["retweetCount"],
                "like_count": row["likeCount"],
                "quote_count": row["quoteCount"],
                "view_count": 0,
            }
            tweets.append(tweet)
        except Exception as e:
            print(f"Error processing row: {row} - {e}")
            # continue
    
    return tweets
    
    

def scrapeMain(numberOfAccounts: int, minutesToScrape: int, parametersFolder: str, cookiesList: list):
    parametersList = splitIntoParts(numberOfAccounts, minutesToScrape)
    tweets_collection = db.tweets

    if os.path.exists(parametersFolder):
        shutil.rmtree(parametersFolder)

    os.makedirs(parametersFolder, exist_ok=True)

    filenames = []
    
    for i, (params, cookiesfile) in enumerate(zip(parametersList, cookiesList)):
        parametersfile = os.path.join(parametersFolder, f"parameters_{i+1}.json")
        outputfile = f"parsed_tweets/output_{i+1}.csv"

        with open(parametersfile, 'w') as f:
            json.dump(params, f, indent=4)
            
        filenames.append([outputfile, parametersfile, cookiesfile])

    start_time = time.time()
    max_duration = minutesToScrape * 60 / 2
    
    with multiprocessing.Pool(processes=len(filenames)) as pool:
        pool.starmap(process_main, filenames)
    # when a certain amount of time passes, we stop scraping and then call uploadCSV() to upload the CSVs' contents to a mongoDB
    
    elapsed_time = time.time() - start_time
    if elapsed_time >= max_duration:
        print(f"Scraping stopped after {minutesToScrape} minutes.")

    print("Uploading scraped data to MongoDB...")
    for file in os.listdir("parsed_tweets"):
        if file.endswith(".csv"):
            file_path = os.path.join("parsed_tweets", file)
            # use uploadCSV() to upload
            listOfTweets: List[Tweet] = uploadCSV(file_path)
            for tweet in listOfTweets:
                tweet_result = tweets_collection.insert_one(tweet)
                print("\nTweet Test:")
                print("Inserted tweet with id:", tweet_result.inserted_id)
    print("Upload complete.")
    
    

    
if __name__ == "__main__":
    cookiesList = [
        "accounts_cookies/accounts_cookies1.py",
        "accounts_cookies/accounts_cookies2.py",
        "accounts_cookies/accounts_cookies3.py",
        "accounts_cookies/accounts_cookies4.py",
        "accounts_cookies/accounts_cookies5.py",
        "accounts_cookies/accounts_cookies6.py"
    ]

    # scrapeMain(6, 60, "parametersFolder", cookiesList)
    
    # print(uploadCSV("parsed_tweets/output_1.csv"))
    
    # tweets_collection = db.tweets
    # for file in os.listdir("parsed_tweets"):
    #     if file.endswith(".csv"):
    #         file_path = os.path.join("parsed_tweets", file)
    #         listOfTweets: List[Tweet] = uploadCSV(file_path)
    #         for tweet in listOfTweets:
    #             tweet_result = tweets_collection.insert_one(tweet)
    #             print("\nTweet Test:")
    #             print("Inserted tweet with id:", tweet_result.inserted_id)
    # print("Upload complete.")

# print(f"{getTrendingKeywords(CURRENTCOOKIE)}")

# print(f"{splitIntoParts(15, 15)}")