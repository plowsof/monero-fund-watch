
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
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options



ccs_url = "https://repo.getmonero.org/monero-project/ccs-proposals/-/merge_requests/"
binaryFate_url = "https://repo.getmonero.org/users/binaryFate/activity"
cryptocompare.cryptocompare._set_api_key_parameter("-")
consumer_key ="-"
consumer_secret ="-"
access_token ="-"
access_token_secret ="-"

def scrape_page(txid_compare):
    global binaryFate_url
    with Display(visible=False, size=(1200, 1500)):
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        driver.get(binaryFate_url)
        timeout = 10
        try:
            try:
                element_present = EC.presence_of_element_located((By.CLASS_NAME, 'event-item'))
                WebDriverWait(driver, timeout).until(element_present)
            except TimeoutException:
                print("Timed out waiting for page to load")
            fatesPosts = driver.find_elements_by_class_name("event-item")
            return check_txid(txid_compare,fatesPosts)
            pass
        finally:
            driver.quit()
            pass

def check_txid(txid_compare,fatesPosts):
    global ccs_url
    found_txid = 0
    return_list=[1,2]
    for post in fatesPosts:
        if found_txid == 0:
            text_lines = post.text.splitlines()
            #print(text_lines)
            if text_lines[2] == "commented on":
                #its a comment
                data_comment = text_lines[7]
                #check for txid in comment
                words = data_comment.replace(".","").split(" ")
                for x in words:
                    if len(x) == 64:
                        if x == txid_compare:
                            #this is most likely a txid
                            data_txid = x
                            data_ccsid = text_lines[4].replace("!","")
                            #trailing space to avoid any connected dots that break the link
                            actual_ccs = ccs_url+str(data_ccsid)+" " 
                            data_comment = data_comment.replace(data_txid,actual_ccs)
                            #print(data_comment)
                            found_txid = 1
                            break
        else:
            #we found the tx , no need to search further
            break
    if found_txid == 0:
        return_list[0] = 0
        return return_list
    else:
        return_list[0] = 1
        return_list[1] = data_comment
        return return_list

def insertData(amount):
    #add to database
    con = sqlite3.connect('/var/log/monero/general-fund.db')
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
    #loop incase rpc daemon has not started up yet.
    while True:
        try:
            rpc_connection = AuthServiceProxy(service_url='http://127.0.0.1:18084/json_rpc')
            params={"account_index":0,
            "txid":str(tx_id)}
            info = rpc_connection.get_transfer_by_txid(params)
            break
        except Exception as e:
            print(e)
            print("Retrying connection in 5 seconds.")
            time.sleep(5)

    height = info["transfer"]["height"]
    if info["transfer"]["height"] != 0:
        raw_amount = info["transfer"]["amount"]
        memelord = 0
        if "420" in str(raw_amount) or "69" in str(raw_amount):
            memelord = 1
        amount = formatAmount(raw_amount)
        validateInput(amount,tx_id,memelord)
        
    else:
        print("New tx in mem pool, waiting for confirmations")

#validate inputs by seeking the txid in binaryFates comments
def validateInput(amount,tx_id,ml):
    print("sleep an hour")
    time.sleep(3600)
    pull_data = scrape_page(tx_id)
    if pull_data[0] == 1:
        #the tx_id was found in binaryFates comments 
        sendTweet(pull_data[1])
    else:
        #normal tweet
        makeTweet(amount,ml)
        insertData(amount)
        saveWallet()


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
    #https://stackoverflow.com/questions/5807952/removing-trailing-zeros-in-python
    return str(float(s))

def makeTweet(amount,memelord):
    fiatValue = getPrice("XMR",amount)
    tweet = emoji.emojize(f':heart_with_ribbon: +{amount} #xmr :heart_with_ribbon: ${fiatValue}')
    #check fiat value for memelord status
    if "420" in str(fiatValue) or "69" in str(fiatValue):
        memelord = 1
    if memelord == 1:
        tweet += emoji.emojize(' :winking_face:')
    sendTweet(tweet)

def sendTweet(tweet):
    global consumer_key, consumer_secret, access_token, access_token_secret
    # authentication of consumer key and secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    # authentication of access token and secret
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    # update the status
    #tweepy.error.TweepError: [{'code': 187, 'message': 'Status is a duplicate.'}]
    while True:
        try:
            api.update_status(status = tweet)
            break
        except Exception as e:
            print(e)
            tweet += " " + random.choice(string.ascii_letters)
            time.sleep(1)

def saveWallet():
    #not sure how often the rpc wallet saves automatically 
    try:
        rpc_connection = AuthServiceProxy(service_url='http://127.0.0.1:18084/json_rpc')
        rpc_connection.store()
        pass
    except Exception as e:
        raise e

def main(tx_id):
    checkHeight(str(tx_id))

if __name__ == '__main__':
    tx_id = sys.argv[1]
    main(tx_id)

'''
sqlite> create table main (
   ...> amount INTEGER NOT NULL,
   ...> date_time TEXT NOT NULL
   ...> );
'''
