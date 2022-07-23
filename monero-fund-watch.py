
#delayed donation updates 1 hour to check for change outputs
import sys
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException
from pprint import pprint
import tweepy
import emoji
import json
import sqlite3
from datetime import datetime
import time
import random
import string
import cryptocompare
import pickle
import os
import requests
from bs4 import BeautifulSoup
import json
import pprint
from matrix_client.api import MatrixHttpApi

import asyncio

m_access_token = ""
instance = ""

#from pyvirtualdisplay import Display
import traceback 
ccs_url = "https://repo.getmonero.org/monero-project/ccs-proposals/-/merge_requests/"
binaryFate_url = "https://repo.getmonero.org/users/binaryFate/activity?limit=20&offset=0"
#binaryFate_url = "https://repo.getmonero.org/users/binaryFate"
cryptocompare.cryptocompare._set_api_key_parameter("44ecd590024044271c33b1ad36529f2d5b90773a3454906c0aece462b95042c6")

consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

pickled_data = "/var/log/monero/pickled_data.pkl"
node_url =  'http://localhost:18084/json_rpc'
loc_db = "/var/log/monero/general-fund.db"
tweetFile = "/var/log/monero/tweet"
blockchain_explorer = "https://www.exploremonero.com/transaction/"
loc_long = 55.4920
loc_lat = -4.6796
'''
pickled_data = "pickled_data.pkl"
node_url =  'http://localhost:18084/json_rpc'
loc_db = "general-fund.db"
tweetFile = "tweet"
'''
def logit(sometext):
    global tweetFile
    with open(tweetFile, "a+") as f:
        f.write(str(sometext) + "\n")
        
def requests_scrape_page(txList):
    global binaryFate_url
    global ccs_url
    while True:
        try:
            myDict = {
                'accept': 'application/json, text/plain, */*',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
                }
            r=requests.get(binaryFate_url, headers=myDict).text
            #pprint.pprint(r)
            someDict = json.loads(r)
            break
        except:
            time.sleep(2)
            print("failed to download page")
    soup = BeautifulSoup(someDict['html'], 'html.parser')
    #print(soup.prettify())
    strings = soup.find_all(class_='event-body')
    count = 0
    fatesPosts = []
    for each in strings:
        count+=1
        #print("item : " + str(count))
        comment = each.get_text().strip()
        ccs = each.parent.find(class_='event-title').a.get_text()
        #comment = each.parent.find(class_='event-title').a['href']
        #print(f"data2: {ccs}")
        #print(f"data3: {comment}")
        headlist = []
        #print("Hello")
        #pprint.pprint(txList)
        for tx in txList:
            headlist.append(tx[0][0:6])
        pprint.pprint(headlist)
        for word in comment.replace(".","").split(" "):
            if len(word) < 6:
                continue
            if word[0:6] in headlist:
                print("gotem")
                #print(word)
                #this is most likely a txid
                data_txid = word
                data_ccsid = ccs.replace("!","")
                #trailing space to avoid any connected dots that break the link
                actual_ccs = ccs_url+str(data_ccsid)+" " 
                data_comment = comment.replace(data_txid,actual_ccs).replace("...","")
                data = []
                #print(data_comment)
                #print(data_txid)
                #print(data_comment)
                data.append(data_txid)
                data.append(data_comment)
                fatesPosts.append(data)
                #pprint.pprint(fatesPosts)
                #logit(data_comment)

    #Search matrix chat and append to fatesPosts
    matrix = MatrixHttpApi("https://matrix.org", token="syt_cGxvd3NvZg_QAbIgvAtIbidLSMmTCfU_2PerS4")
    token = None
    moneroRoom = matrix.get_room_messages(room_id="!WzzKmkfUkXPHFERgvm:matrix.org",token=token, direction="b", limit=20, to=None)
    hour_history = int(moneroRoom["chunk"][0]["origin_server_ts"])
    age = hour_history
    hour_history = (hour_history - 3600000)
    matrixPosts = []
    while age > hour_history:
        for x in moneroRoom["chunk"]:
            age = x["origin_server_ts"] #seems to be in MS
            print(f"age now: {age} hour_history {hour_history}")
            if age < hour_history:
              break
            if "body" in x["content"]:
                #print(x["content"]["body"])
                #print(x["user_id"])
                if x["user_id"] == "@binaryFate:libera.chat":
                    comment = x["content"]["body"]
                    #if its from binary fate
                    #if it contains 64 len char = gotem
                    for word in comment.replace(".","").split(" "):
                        if len(word) == 64:
                            data_txid = word
                            data_comment = comment.replace(data_txid,"") #deletes the txid from comment
                            data = []
                            data.append(data_txid)
                            data.append(data_comment)
                            fatesPosts.append(data)
        token = moneroRoom["end"]
        time.sleep(1)
        moneroRoom = matrix.get_room_messages(room_id="!WzzKmkfUkXPHFERgvm:matrix.org",token=token, direction="b", limit=20, to=None)
    #pprint.pprint(fatesPosts)
    return fatesPosts

def insertData(amount):
    #add to database
    global loc_db
    con = sqlite3.connect(loc_db)
    cur = con.cursor()
    date_time = getDateTime()
    # Insert a row of data
    sqlite_insert_with_param = """INSERT INTO main
                          (amount, date_time) 
                          VALUES (?,?);"""
    data = (amount,date_time)
    cur.execute(sqlite_insert_with_param, data)
    con.commit()
    con.close()

def getDateTime():
    now = datetime.now()
    #dd/mm/YY H:M:S
    return now.strftime('%Y-%m-%d %H:%M:%S')

def getPrice(crypto,amount):
    try:
        data = cryptocompare.get_price(str(crypto), currency='USD', full=0)
        #print(f"[{crypto}]:{data[str(crypto)]['USD']}")
        fiatValue = data[str(crypto)]["USD"]
        return(format(fiatValue * float(amount), '.2f'))        
        pass
    except Exception as e:
        #1 xmr = 1 xmr
        raise e
        return ""

def checkHeight(tx_id):
    global pickled_data
    global node_url
    #loop incase rpc daemon has not started up yet.
    while True:
        try:
            rpc_connection = AuthServiceProxy(service_url=node_url)
            params={"account_index":0,
            "txid":str(tx_id)}
            info = rpc_connection.get_transfer_by_txid(params)
            break
        except Exception as e:
            logit(e)
            print(e)
            print("Retrying connection in 5 seconds.")
            time.sleep(5)

    height = info["transfer"]["height"]
    logit(f"height: {height}")
    if info["transfer"]["height"] == 0:
        raw_amount = info["transfer"]["amount"]
        #are we the first transaction? (no pickle file)
        txData = []
        txData.append(tx_id)
        txData.append(raw_amount) 
        if not os.path.isfile(pickled_data):
            #we're the master tx
            txList = []
            txList.append(txData)       
            pickle.dump( txList, open( pickled_data, "wb+" ) )
            #20 minutes
            logit("All aboard..")
            time.sleep(1200)
            #time.sleep(5)
            #load
            txList = pickle.load( open( pickled_data, "rb" ) )
            #delete
            os.remove(pickled_data)
            logit(f"train leaving the station with {len(txList)} passengers")
            time.sleep(2400)
            #time.sleep(5)
            validateInput(txList)
        else:
            #append to existing txList
            txList = pickle.load( open( pickled_data, "rb" ) )
            txList.append(txData)
            pickle.dump( txList, open( pickled_data, "wb+" ) )
    else:
        print("New tx in mem pool, waiting for confirmations")

#validate inputs by seeking the txid in binaryFates comments
def validateInput(txList):
    global tweetFile
    try:
        fatesPosts = requests_scrape_page(txList)
        pprint.pprint(fatesPosts)
        for x in txList:
            tx_id = x[0][0:6]
            raw_amount = x[1]
            memelord = 0
            if "420" in str(raw_amount) or "69" in str(raw_amount):
                memelord = 1
            amount = formatAmount(raw_amount)
            #pull_data = check_txid(tx_id,fatesPosts)
            found = 0
            for x in fatesPosts:
                compare_txid = x[0]
                comment = x[1]
                #print(f"Is {tx_id} == {compare_txid}")
                if tx_id in compare_txid:
                    found = 1
                    break
            if found == 1:
                pass
                sendTweet(comment,1)
            else:
                #normal tweet
                makeTweet(amount,memelord)
                insertData(amount)
                saveWallet()
            time.sleep(5)
            pass
    except Exception as e:
        raise e
        with open(tweetFile, "a+") as f:
            f.write(str(e))
    print("hello  world")



def formatAmount(amount):
    """decode cryptonote amount format to user friendly format.
    Based on C++ code:
    https://github.com/monero-project/bitmonero/blob/master/src/cryptonote_core/cryptonote_format_utils.cpp#L751
    """
    CRYPTONOTE_DISPLAY_DECIMAL_POINT = 12
    s = str(amount)
    if len(s) < CRYPTONOTE_DISPLAY_DECIMAL_POINT + 1:
        # add some trailing zeros, if needed, to have constant width
        s = '0' * (CRYPTONOTE_DISPLAY_DECIMAL_POINT + 1 - len(s)) + s
    idx = len(s) - CRYPTONOTE_DISPLAY_DECIMAL_POINT
    s = s[0:idx] + "." + s[idx:]
    #my own hack to remove trailing 0's, and to fix the 1.1e-5 etc
    trailing = 0
    while trailing == 0:
        if s[-1:] == "0":
            s = s[:-1]
        else:
            trailing = 1
    return s

def makeTweet(amount,memelord):
    global blockchain_explorer
    fiatValue = getPrice("XMR",amount)
    tweet = emoji.emojize(f':heart_with_ribbon: +{amount} #xmr :heart_with_ribbon: ${fiatValue}')
    #check fiat value for memelord status
    if "420" in str(fiatValue) or "69" in str(fiatValue):
        memelord = 1
    if float(fiatValue) == 0.00:
        tweet += emoji.emojize(' :whale: :police_car_light:')
    if memelord == 1:
        tweet += emoji.emojize(' :winking_face:')
    tweet += f"\n\n{blockchain_explorer}" + tx_id
    sendTweet(tweet)
    print(f"TWEETED {tweet}")

def sendTweet(tweet,url_preview=0):
    global consumer_key, consumer_secret, access_token, access_token_secret
    global tweetFile
    global loc_long, loc_lat
    # authentication of consumer key and secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    # authentication of access token and secret
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    # update the status
    #tweepy.error.TweepError: [{'code': 187, 'message': 'Status is a duplicate.'}]
    while True:
        try:
            if url_preview == 0:
                api.update_status(status = tweet, card_uri='tombstone://card', long=loc_long, lat=loc_lat, display_coordinates=1 )
            else:
                api.update_status(status = tweet, lat=loc_lat, long=loc_long, display_coordinates=1 )
            with open(tweetFile, "a+") as f:
                f.write(tweet + "\n")
            print(tweet)
            #asyncio.run(mastodon_toot(tweet))
            break
        except Exception as e:
            print(e)
            tweet += " " + random.choice(string.ascii_letters)
            time.sleep(60)

async def mastodon_toot(msg):
    global m_access_token, instance
    async with atoot.client(instance, access_token=m_access_token) as c:
        await c.create_status(status=msg)

def saveWallet():
    #not sure how often the rpc wallet saves automatically 
    try:
        rpc_connection = AuthServiceProxy(service_url=node_url)
        rpc_connection.store()
        pass
    except Exceptio:
        raise e

def main(tx_id):
    global tweetFile
    try:
        with open(tweetFile, "a+") as f:
            f.write("We have been called!\n")
        checkHeight(str(tx_id))
        pass
    except Exception:
        with open(tweetFile, "a+") as f:
            f.write(str(traceback.print_exc()) + "\n")
    

if __name__ == '__main__':
    #logit("ok some sanity")
    tx_id = sys.argv[1]
    #tx_id = "7d11dcef0c2608ecd099cd689c0e0a010841a399014a35a153e6bf5430a1f011"
    main(tx_id)
    #asyncio.run(mastodon_toot("hello"))
'''
sqlite> create table main (
   ...> amount INTEGER NOT NULL,
   ...> date_time TEXT NOT NULL
   ...> '''

