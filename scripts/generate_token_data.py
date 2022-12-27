import time, re, json, requests, datetime, time, os, telebot
from multicall import Call, Multicall
from dotenv import load_dotenv, find_dotenv
from brownie import (Contract, accounts, ZERO_ADDRESS, chain, web3, interface, ZERO_ADDRESS)

def generate_token_data(TARGET_USD_VALUE):
    f = open('th_approved_tokens.json')
    tokens = json.load(f)
    oracle = Contract("0x83d95e0D5f402511dB06817Aff3f9eA88224B030")
    helper = Contract("0x52CbF68959e082565e7fd4bBb23D9Ccfb8C8C057")
    vaults = list(helper.getVaults())
    for v in vaults:
        tokens[v] = Contract(v).symbol()
    data = {}
    for t in tokens:
        try:
            t = web3.toChecksumAddress(t)
            token = Contract(t)
            p = oracle.getPriceUsdcRecommended(t) / 1e6
            decimals = token.decimals()
            symbol = token.symbol()
            if symbol == 0x4d4b520000000000000000000000000000000000000000000000000000000000:
                symbol = "MKR"
            if p == 0:
                continue
            threshold = (TARGET_USD_VALUE / p) * 10 ** decimals
            print(f'{symbol} {threshold/10**decimals}')
            data[t] = {}
            data[t]['symbol'] = symbol
            data[t]['threshold'] = threshold
        except:
            continue
    data['last_updated'] = int(time.time())
    f = open("sweep_tokens_list.json", "w")
    f.write(json.dumps(data, indent=2))
    f.close()

if __name__ == '__main__':
    # test1.py executed as script
    # do something
    generate_token_data()