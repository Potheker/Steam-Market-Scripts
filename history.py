# This script looks through a portion of your steam market history (find the start and end index by going to your history in the browser,
# and click through the history. If you e.g. want to have pages 5-7 you would set start = 50, end = 69. Also set the game name and appid)
# It then catalogues how much money you spent and the current value of the items you bought.
# Set marketfee = True to exclude steam market fee from the value

import requests
import re
import numpy as np
cookie = {'steamLoginSecure': ''} 
appid = 730
game = 'Counter-Strike: Global Offensive'
start = 0
end = 10359
marketfee = False

# Setup Dict
total = dict() 

try:
    cookie_file = open('history.ini','r+')
except:
    cookie_file = open('history.ini','w+')
file_content = cookie_file.read()
cookie_invalid = True
while cookie_invalid:
    if len(file_content) < 2:
        # File doesn't exist or is invalid
        print('Please enter \"steamLoginSecure\" cookie: ')
        cookie_in = input()
        cookie['steamLoginSecure'] = cookie_in
        # Delete and overwrite content
        cookie_file.truncate(0)
        cookie_file.write('[cookie]\nsteamLoginSecure = ')
        cookie_file.write(cookie_in)
    else:
        cookie['steamLoginSecure'] = file_content[file_content.index(" = ")+3:]
        file_content = []  # We set this so that the file isn't read again if the cookie doesn't work

    # We try a simple request to get the total number of transactions (=n)  
    params = {'start':0,'count':1}
    response = requests.get('https://steamcommunity.com/market/myhistory', params=params, cookies = cookie).text
    if len(response) > 3000:
        cookie_invalid = False
    else:
        print("Cookie invalid")
cookie_file.close()
n = int(response[response.index("total_count")+13 : response.index("start")-2])
print("Found ",n, " Transactions")


# Each step is one request with 500 items
for i in range(start,end+1,500):

    # make request
    params = {'start':i,'count':500}
    response = requests.get('https://steamcommunity.com/market/myhistory', params=params, cookies = cookie).text
    response = response[response.index('\"hovers\"') : ]
    response = re.split("market_listing_item_img",response)
    response = response[1:]
    

    # go over every entry
    for j,res in enumerate(response):

        if(j+i > end):
            break

        #Listing a new Item or canceling a Listing have their own entry. We skip them.
        if ('created' in res) or ('canceled' in res) or (game not in res):
            continue

        # Find Item Name through RegEx
        item = re.search(r'market_listing_item_name\\.+?>(.+?)<', res).group(1)
        
        # Find Price through RegEx
        price = float(re.search('market_listing_price.+?([0-9]+,[0-9-]+)€', res).group(1).replace(',','.').replace('-','0'))
        
        if "Seller:" in res:
            #Code for a Buy entry
            if item in total:
                (a,b) = total[item]
                total[item] = (a+1,b+price)
            else:
                total[item] = (1,price)

# Calculate value
spent = 0
value = 0
for item in total:
    (count,price) = total[item]
    spent += price
    params = {'currency':3,'appid':appid,'market_hash_name':item}
    res = requests.get('https://steamcommunity.com/market/priceoverview', params=params, cookies = cookie).text
    newprice = float(re.search('"lowest_price":"([0-9]+,[0-9-]+)€',res).group(1).replace(',','.').replace('-','0'))
    if(marketfee):
        newprice -= max(np.floor(round(newprice/11.5,3)*100)/100,0.01) + max(np.floor(round(newprice/23,3)*100)/100,0.01)
    value += newprice*count
    print("{count}x {item} for {price:.3f}€ now worth {new:.2f}€".format(count = count, item = item, price = price/count, new=newprice))

print('Total spent: {spent:.2f}€'.format(spent = spent))
print('Value: {value:.2f}€'.format(value = value))
