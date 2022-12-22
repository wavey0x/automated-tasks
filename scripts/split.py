import time, re, json, requests, datetime, time, os, telebot
from dotenv import load_dotenv, find_dotenv
from brownie import (Contract, accounts, ZERO_ADDRESS, chain, web3, interface, ZERO_ADDRESS)

load_dotenv(find_dotenv())
telegram_bot_key = os.environ.get('WAVEY_ALERTS_BOT_KEY')
env = 'PROD' if os.environ.get('ENV') == 'PROD' else 'DEV'
bot = telebot.TeleBot(telegram_bot_key)
CHAT_IDS = {
    "WAVEY_ALERTS": "-789090497",
    "CURVE_WARS": "-1001712241544",
    "GNOSIS_CHAIN_POC": "-1001516144118",
    "YBRIBE": "-1001862925311",
    "VEYFI": "-1001558128423",
}

def main():
    # setup()
    bribe_splitter()

def setup():
    ytrades = accounts.at(web3.ens.resolve('ytrades.ychad.eth'), force=True)
    automation_eoa = '0xA009Cf8B0eDddf58A3c32Be2D85859fA494b12e3'
    bribe_splitter = Contract(web3.ens.resolve('bribe-splitter.ychad.eth'), owner=web3.ens.resolve('ychad.eth'))
    bribe_splitter.setOperator(automation_eoa, True)
    spell = Contract('0x090185f2135308BaD17527004364eBcC2D37e5F6',owner=ytrades)
    spell.transfer(bribe_splitter,spell.balanceOf(ytrades))
    treasury = accounts.at(web3.ens.resolve('treasury.ychad.eth'), force=True)
    crv = Contract('0xD533a949740bb3306d119CC777fa900bA034cd52',owner=treasury)
    crv.transfer(bribe_splitter,crv.balanceOf(treasury))

def bribe_splitter():
    worker = accounts.load('automate')
    bribe_splitter = Contract(web3.ens.resolve('bribe-splitter.ychad.eth'), owner=worker)
    ybribe = Contract(web3.ens.resolve('ybribe.ychad.eth'))
    voter = Contract(web3.ens.resolve('curve-voter.ychad.eth'))
    f = open('splitter.json')
    data = json.load(f)
    st_balance = Contract('0x27B5739e22ad9033bcBf192059122d163b60349D').totalAssets()
    result = {}
    for token_address in data:
        token = Contract(token_address)
        gauge = data[token_address]['gauge']
        should_claim = data[token_address]['should_claim']
        balance = token.balanceOf(bribe_splitter)
        print(f'{token.symbol()} balance: {balance/10**token.decimals()}')
        if balance > 0:
            if should_claim and ybribe.claimable(voter, gauge, token_address) > 0:
                should_claim = True
            else:
                should_claim = False
            tx = bribe_splitter.bribesSplitWithManualStBalance(token_address, gauge, st_balance, should_claim)
            output = print_results(tx, token_address, bribe_splitter, gauge, token.address)
            result[token_address] = output
    print(result)
    for r in result:
        t = result[r]
        split = t['split']
        msg = f'🖖 Bribe Split Detected!\n'
        split['refund']['amount']
        abbr, link, r_markdown = abbreviate_address(split['refund']['target'])
        abbr, link, t_markdown = abbreviate_address(split['treasury']['target'])
        abbr, link, y_markdown = abbreviate_address(split['ycrv']['target'])
        refund_amt = round(split['refund']['amount'] / 10 ** t['token_decimals'],2)
        ycrv_amt = round(split['ycrv']['amount'] / 10 ** t['token_decimals'],2)
        treasury_amt = round(split['treasury']['amount'] / 10 ** t['token_decimals'],2)
        msg += f'\nTreasury: {treasury_amt:,} {t["token_symbol"]} -> {t_markdown}'
        msg += f'\nYCRV: {ycrv_amt:,} {t["token_symbol"]} -> {y_markdown}'
        msg += f'\nRefund: {refund_amt:,} {t["token_symbol"]} -> {r_markdown}'
        txn_hash = t['txn_hash']
        msg += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{txn_hash})'
        t['split']['refund']
        chat_id = CHAT_IDS["WAVEY_ALERTS"]
        if env == 'PROD':
            chat_id = CHAT_IDS["CURVE_WARS"]
        bot.send_message(chat_id, msg, parse_mode="markdown", disable_web_page_preview = True)

def print_results(tx, token_address, splitter, gauge, token):
    refund_recipient = splitter.refundRecipient(gauge, token)
    treasury = splitter.yearnTreasury()
    ycrv_target = splitter.stYcrvStrategy()
    output = {
        'token_symbol': Contract(token_address).symbol(),
        'token_decimals': Contract(token_address).decimals(),
        'gauge': gauge,
        'txn_hash': tx.txid,
        'total_amount': 0,
        'split': {
            'treasury': {
                'amount': 0,
                'target': treasury,
            },
            'ycrv': {
                'amount': 0,
                'target': ycrv_target,
            },
            'refund': {
                'amount': 0,
                'target': refund_recipient,
            },
        }
    }
    for e in tx.events['Transfer']:
        token = Contract(e.address)
        _from = e[e.keys()[0]]
        if _from == splitter.address:
            total_amount = 0
            _to = e[e.keys()[1]]
            amount = e[e.keys()[2]]
            total_amount += amount
            decimals = token.decimals()
            if _to == treasury:
                output['split']['treasury']['amount'] = amount
            if _to == refund_recipient:
                output['split']['refund']['amount'] = amount
            if _to == ycrv_target:
                output['split']['ycrv']['amount'] = amount
    output['total_amount'] = total_amount
    return output

def abbreviate_address(address):
    abbr = address[0:7]
    link = f'https://etherscan.io/address/{address}'
    markdown = f'[{abbr}...]({link})'
    return abbr, link, markdown