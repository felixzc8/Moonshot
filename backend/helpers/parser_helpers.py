from collections import defaultdict
import json
import re
import traceback
import time
import numpy as np
from datetime import datetime

def basic_tweet_content(tweet, tweet_type):
    tweet_result  = None
    if tweet["itemContent"]["tweet_results"]["result"]["__typename"] == "Tweet":
         tweet_result = tweet["itemContent"]["tweet_results"]["result"]
    elif tweet["itemContent"]["tweet_results"]["result"]["__typename"] == "TweetWithVisibilityResults":
         tweet_result = tweet["itemContent"]["tweet_results"]["result"]["tweet"]
    else:
        raise Exception(f"Error: A new type of tweet encountered - {tweet}")

    response = tweet_result

    tweet_id = tweet_result["rest_id"]
    tweet_user_data = tweet_result["core"]["user_results"]["result"]["legacy"]
    tweet_user_name = tweet_user_data["screen_name"]
    tweet_legacy_key_data = tweet_result["legacy"]
    tweet_text = tweet_legacy_key_data["full_text"]
    tweet_url = f"https://twitter.com/{tweet_user_name}/status/{tweet_id}"
    tweet_legacy_entities = tweet_legacy_key_data["entities"]
    tweet_create_date_obj = datetime.strptime(tweet_legacy_key_data["created_at"], "%a %b %d %H:%M:%S %z %Y")
    tweet_epoch = int(tweet_create_date_obj.timestamp())
    tweet_legacy_entities_media = []
    if "media" in tweet_legacy_entities:
        tweet_legacy_entities_media = tweet_legacy_entities["media"]
    tweet_data = {
        "type":tweet_type,
        "id":tweet_id,
        "username":tweet_user_name,
        "text":tweet_text,
        "url":tweet_url,
        "epoch": tweet_epoch,
        "media":tweet_legacy_entities_media
    }
    
    if "legacy" in tweet["itemContent"]["tweet_results"]["result"] and "retweeted_status_result" in tweet["itemContent"]["tweet_results"]["result"]["legacy"]:
        tweet_data['retweetedTweet'] = True
        retweeted_tweet = tweet["itemContent"]["tweet_results"]["result"]["legacy"]["retweeted_status_result"]
        tweet_data["retweetedTweetID"] = str(retweeted_tweet["result"]["rest_id"])
        tweet_data["retweetedUserID"] = str(retweeted_tweet["result"]["core"]["user_results"]["result"]["rest_id"])
    else:
        tweet_data['retweetedTweet'] = False
        tweet_data["retweetedTweetID"] = np.nan
        tweet_data["retweetedUserID"] = np.nan

    tweet_data['id_str'] = str(tweet_data['id'])
    tweet_data['lang'] = tweet_legacy_key_data['lang']
    tweet_data['rawContent'] = tweet_legacy_key_data['full_text']
    tweet_data['replyCount'] =tweet_legacy_key_data['reply_count']
    tweet_data['retweetCount'] = tweet_legacy_key_data['retweet_count']
    tweet_data['likeCount'] = tweet_legacy_key_data['favorite_count']
    tweet_data['quoteCount'] = tweet_legacy_key_data['quote_count']
    tweet_data['conversationId'] = tweet_legacy_key_data['conversation_id_str']
    tweet_data['conversationIdStr'] = tweet_data['conversationId']
    tweet_data['hashtags'] = tweet_legacy_key_data['entities']['hashtags']
    tweet_data['mentionedUsers'] =tweet_legacy_key_data['entities']['user_mentions']
    tweet_data['links'] = tweet_legacy_key_data['entities']['urls']
    tweet_data['viewCount'] = tweet_result['views']
    
    tweet_data['quotedTweet'] = response['legacy']['is_quote_status']

    nf_fields = [
        'in_reply_to_screen_name', 'in_reply_to_status_id_str', 'in_reply_to_user_id_str'
        , 'location', 'cash_app_handle'
    ]
    for field in nf_fields:
        tweet_data[field] = tweet_legacy_key_data.get(field, "")

    # User Populate
    user_record = response['core']['user_results']['result']

    tweet_data['user'] = {
        'id':int(tweet_legacy_key_data['user_id_str']),
        'id_str':tweet_legacy_key_data['user_id_str'],
        'url': f"https://twitter.com/{user_record['legacy']['name']}",
        'username':user_record['legacy']['name'],
        'rawDescription':user_record['legacy']['description'],
        'created':datetime.strptime(user_record['legacy']["created_at"], "%a %b %d %H:%M:%S %z %Y"),
        'followersCount':user_record['legacy']['followers_count'],
        'friendsCount':user_record['legacy']['friends_count'],
        'statusesCount':user_record['legacy']['statuses_count'],
        'favouritesCount':user_record['legacy']['favourites_count'],
        'listedCount':user_record['legacy']['listed_count'],
        'mediaCount':user_record['legacy']['media_count'],
        'location':user_record['legacy']['location'],
        'profileImageUrl':user_record['legacy']['profile_image_url_https'],
        'profileBannerUrl':"PW",
        'protected':"PW",
        'verified':user_record['legacy']['verified'],
        'blue':user_record['is_blue_verified'],
        'blueType':None,
        'descriptionLinks':["PW"],
        '_type':'PW'
        }
    
    tweet_data['user'] = str(tweet_data['user'])

    return tweet_data

def parse_tweet_contents(tweet):
    # types!!!! dealing with type: tweet-1799120923716354252 (type - tweet)
   # this one just caters to tweet with just media and text (doesn't deal with quotations, threads)
    tweets = []

    try:
        if tweet["entryId"].startswith("profile-conversation"):
            for i in range(len(tweet["content"]["items"])):
                tweets.append(basic_tweet_content(tweet["content"]["items"][i]["item"], re.sub(r'\d+', '', tweet["entryId"])))
        elif tweet["entryId"].startswith("tweet-"):
            tweets.append(basic_tweet_content(tweet["content"],re.sub(r'\d+', '', tweet["entryId"])))
        else:
            print(tweet["entryId"])

        if len(tweets) == 1:
                return tweets[0]
    except Exception as e:
        with open('errorfile.json', 'w') as f:
            json.dump(tweet, f)
        stack_trace = traceback.format_exc()
        # Print or log the stack trace
        print(f"An error occurred: {e}")
        print(stack_trace)
    return tweets

def parse_search_timeline_response(data):
    timeline = data['search_timeline']["timeline"]
    instructions = timeline["instructions"]
    tweets = []
    for i in range(len(instructions)):
        if instructions[i]["type"]=="TimelineAddEntries":
            entries = instructions[i]["entries"]
            for j in range(len(entries)):
                result = parse_tweet_contents(entries[j])
                if len(result)!=0:
                    tweets.append(result)
    last_tweet_epoch = None
    if len(tweets)!=0:
        last_tweet_epoch = tweets[len(tweets)-1]["epoch"]
    return {"data":tweets, "tweet_count":len(tweets), "last_tweet_epoch":last_tweet_epoch}

def parse_response(data):
    timeline = data["timeline_v2"]["timeline"]
    instructions = timeline["instructions"]
    tweets = []
    for i in range(len(instructions)):
        if instructions[i]["type"]=="TimelineAddEntries":
            entries = instructions[i]["entries"]
            for j in range(len(entries)):
                tweets.append(parse_tweet_contents(entries[j]))
   
    return tweets

def test_json():
    with open("data.json","r") as file:
        tweets = parse_response(json.load(file))
        with open("data_preprocessed.json", "w") as f:
            json.dump(tweets, f)