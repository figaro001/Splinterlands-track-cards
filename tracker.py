import requests
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
    return card in info
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

def getDataTransaction(_data={}):
    """
    return transaction datas
    """
    datas_list = []

    if _data != {}:
        for i in _data["items"]:
            resp = requests.get(api["items_sells"]+str(i))
            resp = json.loads(resp.text)
            data_i = {
                "num_cards":resp["num_cards"],
                "currency":resp["currency"],
                "buy_price":resp["buy_price"],
                "cards": [getCard(c) for c in resp["cards"]]
            } 

            datas_list.append(data_i)

    return datas_list

def getMarketPurchaseTransactions(last_block=None):
    """
    return all market purchase transaction made during the last_block_api and last_block
    """

    transactions_list = []

    if last_block is None:
        last_block = getLastBlock()

    # print(f"last block: {last_block}")
    minB = last_block
    # print(f"min block: {minB}")

    resp = requests.get(api["history_blocks"]+str(minB))
    resp = json.loads(resp.text)

    try:
        maxB = resp[len(resp)-1]["block_num"]
        # print(f"max block: {maxB}")
    except:
        return []

    resp = [x for x in resp if x["type"] == "market_purchase"]
    resp = [x for x in resp if x["player"] != x["affected_player"]]
    # print(f"response: {resp}")

    for x in resp:
        transaction = {
            "buyer": x["player"],
            "seller": x["affected_player"],
            "block_id": x["block_id"],
            "block_num": x["block_num"],
            "created_date": x["created_date"],
            "data": getDataTransaction(json.loads(x["data"]))
        }

        transactions_list.append(transaction)

    if maxB < last_block_api:
        transactions_list + getMarketPurchaseTransactions(maxB)

    return transactions_list

if __name__ == "__main__":
    last_block_api = getLastBlock()
    last_block = last_block_api
    while True:
        last_block_api = getLastBlock()
        if last_block != last_block_api:
            print(getMarketPurchaseTransactions(last_block))
            last_block = last_block_api