import time, re, json, requests, datetime, time, os, telebot, scripts.generate_token_data
from multicall import Call, Multicall
from dotenv import load_dotenv, find_dotenv
from brownie import (Contract, accounts, ZERO_ADDRESS, chain, web3, interface, ZERO_ADDRESS)

load_dotenv(find_dotenv())
AUTOMATION_EOA = '0xA009Cf8B0eDddf58A3c32Be2D85859fA494b12e3'
telegram_bot_key = os.environ.get('WAVEY_ALERTS_BOT_KEY')
PASS = os.environ.get('PASS')
worker = accounts.load('automate', PASS)
tx_params = {}
tx_params['max_fee'] = 80e9
tx_params['priority_fee'] = 3e9
telegram_bot_key = os.environ.get('WAVEY_ALERTS_BOT_KEY')
env = 'PROD' if os.environ.get('ENV') == 'PROD' else 'DEV'
bot = telebot.TeleBot(telegram_bot_key)
CHAT_IDS = {
    "WAVEY_ALERTS": "-789090497",
    "CURVE_WARS": "-1001712241544",
    "SEASOLVER": "-1001516144118",
    "YBRIBE": "-1001862925311",
    "VEYFI": "-1001558128423",
}

def main():
    claim_bribes()
    yearn_fed()
    bribe_splitter()
    th_sweeper()
    temple_split()
    ycrv_donator()

def claim_bribes():
    voters, gauges, tokens = ([] for i in range(3))
    claims = [
        {
            'gauge': '0xd8b712d29381748dB89c36BCa0138d7c75866ddF',
            'token': '0x090185f2135308BaD17527004364eBcC2D37e5F6',
        },
    ]
    ybribe = Contract(web3.ens.resolve('ybribe.ychad.eth'),owner=worker)
    voter = Contract(web3.ens.resolve('curve-voter.ychad.eth'),owner=worker)
    claims_to_make = 0
    for c in claims:
        gauge = c['gauge']
        token = c['token']
        if ybribe.claimable(voter, gauge, token):
            claims_to_make += 1
            voters.append(voter)
            gauges.append(gauge)
            tokens.append(token)
    if claims_to_make > 0:
        try:
            tx = ybribe.claim_reward_for_many(voters, gauges, tokens, tx_params)
            m = f'🤖 {claims_to_make} Bribe Claim(s) Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['WAVEY_ALERTS'], m, True)
        except Exception as e:
            transaction_failure(e)
    else:
        print(f'No ybribe claims available.',flush=True)

def yearn_fed():
    puller = interface.IPuller('0xb7e60DAB3799E238D01e0F90c4506eef8F6A1503',owner=worker)
    strat = Contract('0x57505ac8Dac3ce916A48b115e4003dc5587372c7',owner=worker)
    token = Contract(strat.vault())
    if token.balanceOf(strat) > 10e18:
        try:
            tx = puller.pull(token, strat, tx_params)
            m = f'🤳 Reward Pull Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['WAVEY_ALERTS'], m, True)
        except Exception as e:
            transaction_failure(e)
    else:
        print(f'No rewards balance to pull.',flush=True)

def ycrv_donator():
    donator = Contract('0xc368Ed8EfC69D8e38ED4b4d726C40F9F9AD28839', owner=worker)
    if donator.canDonate():
        try:
            tx = donator.donate(tx_params)
            m = f'🫴 Donation Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['WAVEY_ALERTS'], m, True)
        except Exception as e:
            transaction_failure(e)

def temple_split():
    WEEK = 60 * 60 * 24 * 7
    split = Contract('0x77Ff318a33cf832671D2F9E0393cd1f854Fe8111', owner=worker)
    current_week = int(chain.time() / WEEK) * WEEK
    if current_week > split.period()['period']:
        try:
            tx = split.split(tx_params)
            m = f'🕍 Temple Split Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['WAVEY_ALERTS'], m, True)
        except Exception as e:
            transaction_failure(e)

def setup_test():
    ytrades = accounts.at(web3.ens.resolve('ytrades.ychad.eth'), force=True)
    bribe_splitter = Contract(web3.ens.resolve('bribe-splitter.ychad.eth'), owner=web3.ens.resolve('ychad.eth'))
    bribe_splitter.setOperator(AUTOMATION_EOA, True)
    spell = Contract('0x090185f2135308BaD17527004364eBcC2D37e5F6',owner=ytrades)
    spell.transfer(bribe_splitter,spell.balanceOf(ytrades))
    treasury = accounts.at(web3.ens.resolve('treasury.ychad.eth'), force=True)
    crv = Contract('0xD533a949740bb3306d119CC777fa900bA034cd52',owner=treasury)
    crv.transfer(bribe_splitter,crv.balanceOf(treasury))
    ychad = accounts.at(web3.ens.resolve('ychad.eth'), force=True)
    usdt = Contract('0xdAC17F958D2ee523a2206206994597C13D831ec7', owner=ychad)
    th = '0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b'
    usdt.transfer(th, 100e6)
    # sweeper = Contract('0xCca030157c6378eD2C18b46e194f10e9Ad01fa8d', owner=worker)
    # tx = sweeper.sweep([usdt.address], [100e6], txn_params)

def bribe_splitter():
    bribe_splitter = Contract(web3.ens.resolve('bribe-splitter.ychad.eth'), owner=worker)
    ybribe = Contract(web3.ens.resolve('ybribe.ychad.eth'))
    voter = Contract(web3.ens.resolve('curve-voter.ychad.eth'))
    f = open('splitter.json')
    data = json.load(f)
    st_balance = Contract('0x27B5739e22ad9033bcBf192059122d163b60349D').totalAssets()
    for token_address in data:
        token = Contract(token_address)
        gauge = data[token_address]['gauge']
        should_claim = data[token_address]['should_claim']
        split_threshold = data[token_address]['split_threshold']
        balance = token.balanceOf(bribe_splitter)
        symbol = token.symbol()
        print(f'{symbol} balance: {balance/10**token.decimals()} threshold: {split_threshold/10**token.decimals()}',flush=True)
        if balance > split_threshold:
            if should_claim and ybribe.claimable(voter, gauge, token_address) < 1e18:
                should_claim = False # Override if claim not worth it
            try:
                tx = bribe_splitter.bribesSplitWithManualStBalance(token_address, gauge, st_balance, should_claim, tx_params)
                m = f'🖖 {symbol} Split Detected!'
                m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
                send_alert(CHAT_IDS['CURVE_WARS'], m, True)
            except Exception as e:
                transaction_failure(e)

def th_sweeper():
    f = open('sweep_tokens_list.json')
    try:
        sweep_tokens = json.load(f)
    except:
        get_new_price_data()
        sweep_tokens = json.load(f)
    try:
        last_update = sweep_tokens['last_updated']
    except:
        last_update = 0
    if time.time() - last_update > 60 * 60 * 24:
        get_new_price_data()
    sweeper = Contract('0xCca030157c6378eD2C18b46e194f10e9Ad01fa8d', owner=worker)
    th = '0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b'
    calls, token_list, balance_list = ([] for i in range(3))
    # Use multicall to reduce http requests
    for token_address in sweep_tokens:
        if token_address == 'last_updated':
            continue
        calls.append(
            Call(token_address, ['balanceOf(address)(uint256)', th], [[token_address, None]])
        )
    return_values = Multicall(calls)()
    for token_address in return_values:
        balance = return_values[token_address]
        if balance >= sweep_tokens[token_address]['threshold']:
            token_list.append(token_address)
            balance_list.append(balance)
    print(f'{len(token_list)}/{len(sweep_tokens)} tokens eligible for sweep',flush=True)
    if len(token_list) > 0:
        try:
            tx = sweeper.sweep(token_list, balance_list)
            m = f'🧹 Sweep Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['SEASOLVER'], m, True)
        except Exception as e:
            transaction_failure(e)

def get_new_price_data():
    print(f'Generating new token data...',flush=True)
    TARGET_USD_VALUE = 50
    scripts.generate_token_data.generate_token_data()
    # get_new_price_data.generate_token_data()
    # f = open('th_approved_tokens.json')
    # tokens = json.load(f)
    # oracle = Contract("0x83d95e0D5f402511dB06817Aff3f9eA88224B030")
    # data = {}
    # for t in tokens:
    #     try:
    #         t = web3.toChecksumAddress(t)
    #         token = Contract(t)
    #         p = oracle.getPriceUsdcRecommended(t) / 1e6
    #         decimals = token.decimals()
    #         symbol = token.symbol()
    #         if symbol == 0x4d4b520000000000000000000000000000000000000000000000000000000000:
    #             symbol = "MKR"
    #         threshold = (TARGET_USD_VALUE / p) * 10 ** decimals
    #         # print(f'{symbol} {threshold/10**decimals}')
    #         data[t] = {}
    #         data[t]['symbol'] = symbol
    #         data[t]['threshold'] = threshold
    #     except:
    #         continue
    # f = open("sweep_tokens_list.json", "w")
    # f.write(json.dumps(data, indent=2))
    # f.close()
    # print(f'New token + price data written with timestamp {int(time.time())}',flush=True)

def transaction_failure(e):
    worker = accounts.at(AUTOMATION_EOA, force=True)
    print(e,flush=True)
    bal = worker.balance()
    msg = f'🤬 Unable to send transaction.\n\n🔗 [automation EOA](https://etherscan.io/address/0xA009Cf8B0eDddf58A3c32Be2D85859fA494b12e3)\n\nCurrent ETH balance available: {bal/10**18}'
    send_alert(CHAT_IDS['WAVEY_ALERTS'], msg, False)

def send_alert(chat_id, msg, success):
    bot.send_message(chat_id, msg, parse_mode="markdown", disable_web_page_preview = True)