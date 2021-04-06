import requests
import os, sys
import json

last_block_api = None
last_block = None
api = {
    "last_block":"https://api.splinterlands.io/settings",
    "history_blocks":"https://api.splinterlands.io/transactions/history?from_block=",
    "items_sells":"https://api.splinterlands.io/market/status?id=",
    "card":"https://api.splinterlands.io/cards/find?ids="
}

def getLastBlock():
    """
    Return a string with last block writen on chain
    """
    resp = requests.get(api["last_block"])
    resp = json.loads(resp.text)
    return resp["last_block"]

def getCard(card={}):
    """
    return card info
    """

    if card != {}:
        resp = requests.get(api["card"]+f"{card['uid']}")
        resp = json.loads(resp.text)
        card_i = {
            "uid": resp[0]["uid"],
            "id": resp[0]["card_detail_id"],
            "name": resp[0]["details"]["name"],
            "gold": resp[0]["gold"],
            "edition": resp[0]["edition"],
        }

        return card_i

    return {}

def getDataTransaction(data_={}):
    """
    return transaction data
    """
    data_list = []

    if data_ != {}:
        for i in data_["items"]:
            resp = requests.get(api["items_sells"]+str(i))
            resp = json.loads(resp.text)
            data_i = {
                "num_cards":resp["num_cards"],
                "currency":resp["currency"],
                "buy_price":resp["buy_price"],
                "cards": [getCard(c) for c in resp["cards"]]
            } 

            data_list.append(data_i)

    return data_list


def getMarketPurchaseTransactions(last_block=None):
    """
    return all market purchases transaction made during the last_block_api and last_block
    """

    transactions_list = []

    if last_block is None:
        last_block = getLastBlock()

    minB = last_block

    resp = requests.get(api["history_blocks"]+str(minB))
    resp = json.loads(resp.text)

    try:
        maxB = resp[len(resp)-1]["block_num"]
    except:
        return []

    # only market_purchase
    resp = [x for x in resp if x["type"] == "market_purchase"]
    # only market purchase with seller and buyer different
    resp = [x for x in resp if x["player"] != x["affected_player"]]

    for x in resp:
        transaction = {
            "buyer": x["player"],
            "seller": x["affected_player"],
            # "block_id": x["block_id"],
            # "block_num": x["block_num"],
            "created_date": (x["created_date"].split("T"))[0],
            "data": getDataTransaction(json.loads(x["data"]))
        }

        transactions_list.append(transaction)

    if maxB < last_block_api:
        transactions_list + getMarketPurchaseTransactions(maxB)

    return transactions_list

def getCardValue(cards_list):
    cl = []
    for c in cards_list:
        created_date = c["created_date"]
        num_cards =  len(c["data"])
        currency = c["data"][0]["currency"]
        min_price = min([i["buy_price"] for i in c["data"]])
        max_price = max([i["buy_price"] for i in c["data"]])
        card_id = c["data"][0]["cards"][0]["id"]
        name = c["data"][0]["cards"][0]["name"]
        gold = c["data"][0]["cards"][0]["gold"]
        edition = c["data"][0]["cards"][0]["edition"]

        cl.append({
            "created_date": created_date,
            "num_cards": num_cards,
            "currency": currency,
            "min_price": min_price,
            "max_price": max_price,
            "id": card_id,
            "name": name,
            "gold": gold,
            "edition": edition,
        })
    
    return cl

if __name__ == "__main__":
    if last_block_api == None:
        last_block_api = getLastBlock()
        last_block = last_block_api
    while True:
        last_block_api = getLastBlock()
        if last_block != last_block_api:
            list_sold_cards = getMarketPurchaseTransactions(last_block)
            if list_sold_cards != []:
                cards = getCardValue(list_sold_cards)

                with open(f"{os.getcwd()}/cards.json", 'a') as f:
                    for c in cards:
                        f.write(json.dumps(c, indent=4))
        
        last_block = last_block_api