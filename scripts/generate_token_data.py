import time, re, json, requests, datetime, time, os, telebot
from multicall import Call, Multicall
from dotenv import load_dotenv, find_dotenv
from brownie import (Contract, accounts, ZERO_ADDRESS, chain, web3, interface, ZERO_ADDRESS)
from brownie.exceptions import BrownieEnvironmentWarning, BrownieCompilerWarning
from web3._utils.events import construct_event_topic_set
import warnings
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore", BrownieEnvironmentWarning)
warnings.simplefilter("ignore", BrownieCompilerWarning)
TARGET_USD_VALUE = 10

def needs_approval():
    th = '0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b'
    sweeper = '0xCca030157c6378eD2C18b46e194f10e9Ad01fa8d'
    url = f"https://api.ethplorer.io/getAddressInfo/{th}?apiKey=freekey"
    data = requests.get(url).json()
    tokens = data['tokens']
    to_approve = []
    for t in tokens:
        address = t['tokenInfo']['address']
        token = Contract(address)
        decimals = int(t['tokenInfo']['decimals']) # Returns as a string
        symbol = t['tokenInfo']['symbol']
        balance = t['balance']
        try:
            approved = token.allowance(th, sweeper) > 1e25
            print(f'{"✅" if approved else "🚨"} {address} {symbol} {balance/10**decimals}')
            if not approved:
                to_approve.append(address)
        except:
            print(f'⚠️ {address} No approval func: {symbol} {balance/10**decimals}')
    assert False


def generate_token_data(target_usd_value=TARGET_USD_VALUE):
    tokens = get_tokens()
    oracle = Contract("0x83d95e0D5f402511dB06817Aff3f9eA88224B030")
    data = {}
    for t in tokens:
        try:
            t = web3.toChecksumAddress(t)
            token = Contract(t)
            p = oracle.getPriceUsdcRecommended(t) / 1e6
            decimals = token.decimals()
            if t == '0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2':
                symbol = "MKR"
            else:
                symbol = token.symbol()
            if p == 0:
                continue
            threshold = (target_usd_value / p) * 10 ** decimals
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

def get_tokens():
    write_approvals()
    new_list = []
    f = open('th_approved_tokens.json')
    data = json.load(f)
    for t in data:
        new_list.append(t)
    return new_list

if __name__ == '__main__':
    # test1.py executed as script
    # do something
    generate_token_data(TARGET_USD_VALUE)

def main():
    generate_token_data(TARGET_USD_VALUE)

def write_approvals():
    th = '0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b'
    sweeper = '0x6B3d9Fe074c18a2Fa10a8206670Ef7f65F40ff26'
    yfi = Contract('0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e')
    contract = web3.eth.contract(yfi.address, abi=yfi.abi)
    deploy_block = 14676661
    topics = construct_event_topic_set(
        contract.events.Approval().abi, 
        web3.codec,
        {
            'owner': th,
            'spender': sweeper
        }
    )
    logs = web3.eth.get_logs(
        { 'topics': topics, 'fromBlock': deploy_block, 'toBlock': chain.height }
    )
    events = contract.events.Approval().processReceipt({'logs': logs})
    data = {}
    for e in events:
        owner, spender, value = e.args.values()
        if value > 0:
            token = Contract(e.address)
            try:
                sym = token.symbol()
            except:
                sym = 'MKR'
            if token.address == '0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2':
                sym = 'MKR'
            print(f'{e.address} {sym}')
            data[e.address] = str(sym)
    
    f = open("th_approved_tokens.json", "w")
    f.write(json.dumps(data, indent=2))
    f.close()