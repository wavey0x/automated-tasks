import time, re, json, requests, datetime, time, os, telebot, scripts.generate_token_data, logging
from multicall import Call, Multicall
from multicall.utils import await_awaitable
from y import ERC20
import asyncio

from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from brownie import (Contract, accounts, ZERO_ADDRESS, chain, web3, interface, ZERO_ADDRESS)

# logging.basicConfig(level=logging.DEBUG) 

load_dotenv(find_dotenv())
WEEK = 60 * 60 * 24 * 7
TARGET_USD_VALUE = 10
AUTOMATION_EOA = '0xA009Cf8B0eDddf58A3c32Be2D85859fA494b12e3'
telegram_bot_key = os.environ.get('WAVEY_ALERTS_BOT_KEY')
PASS = os.environ.get('PASS')
worker = accounts.load('automate', PASS)
max_fee = int(int(os.environ.get('MAX_FEE'))*1e9)
priority_fee = int(int(os.environ.get('PRIORITY_FEE'))*1e9)
tx_params = {}
tx_params['max_fee'] = max_fee
tx_params['priority_fee'] = priority_fee

telegram_bot_key = os.environ.get('WAVEY_ALERTS_BOT_KEY')
env = 'PROD' if os.environ.get('ENV') == 'PROD' else 'DEV'
bot = telebot.TeleBot(telegram_bot_key)
CHAT_IDS = {
    "WAVEY_ALERTS": "-789090497",
    "YCRV": "-1001653990357",
    "SEASOLVER": "-1001516144118",
    "YBRIBE": "-1001862925311",
    "VEYFI": "-1001558128423",
    "YLOCKERS": "-1001697527660"
}

ignore_tokens = [
    '0x836A808d4828586A69364065A1e064609F5078c7', # pETH
]

def main():
    th_sweeper()
    # stg_harvest()
    claim_votemarket()
    # claim_bribes()
    # yearn_fed()
    bribe_splitter()
    # temple_split()
    # ycrv_donator()
    claim_warden_bribes()
    claim_prisma_hh()
    distribute_yprisma_fees()
    
def stg_harvest():
    threshold = 200_000e6
    s = Contract('0xE7A8Cbc43a0506d3A328393C1C30548835256d7D', owner=worker)
    if s.estimatedTotalAssets() < 10e6:
        print(f'🥳 We are out!')
        return
    market = Contract('0x38EA452219524Bb87e18dE1C24D3bB59510BD783')
    # token = Contract(s.want())
    available = market.deltaCredit()
    if available > threshold:
        print(f'✅ {available/1e6} available. Sending harvest...')
        try:
            tx = s.harvest()
            m = f'Sent Stargate USDT harvest. {"${:,.2f}".format(available/1e6)}'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['WAVEY_ALERTS'], m, True)
        except:
            m = f'Harvest is blocked'
            # send_alert(CHAT_IDS['WAVEY_ALERTS'], m, True)
    else:
        print(f'❌ {"${:,.2f}".format(available/1e6)} available. Less than {"${:,.2f}".format(threshold/1e6)}')

def claim_votemarket():
    print('Claiming from vote market....')
    buffer_time = 60 * 60 * 3
    week_start = int(chain.time() / WEEK) * WEEK
    if week_start + buffer_time > chain.time():
        return # Only proceed if we've waited the buffer time
    voter = Contract(web3.ens.resolve('curve-voter.ychad.eth'),owner=worker)
    markets = [
        '0x0000000BE1d98523B5469AfF51A1e7b4891c6225',
        '0x7D0F747eb583D43D41897994c983F13eF7459e1f',
        '0x0000000895cB182E6f983eb4D8b4E0Aa0B31Ae4c',
    ]
    for m in markets:
        if m == markets[0]:
            market = interface.IMarket(m)
        market = Contract(m, owner=worker)
        bribe_ids_to_claim = []
        for i in range(0,20000):
            try:
                g = market.bribes(i).dict()['gauge']
            except:
                g = market.bounties(i).dict()['gauge']
            if g == ZERO_ADDRESS:
                break
            if market.claimable(voter, i) > 0:
                bribe_ids_to_claim.append(i)
        if len(bribe_ids_to_claim) > 0:
            try:
                tx = market.claimAllFor(voter, bribe_ids_to_claim, tx_params)
                m = f'🤖 {len(bribe_ids_to_claim)} Bribe Claim(s) Detected!'
                m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
                send_alert(CHAT_IDS['YLOCKERS'], m, True)
            except Exception as e:
                transaction_failure(e)

    

def claim_bribes():
    print('Claiming from ybribe....')
    buffer_time = 60 * 60 * 3
    week_start = int(chain.time() / WEEK) * WEEK
    if week_start + buffer_time > chain.time():
        return # Only proceed if we've waited the buffer time
    voters, gauges, tokens = ([] for i in range(3))
    claims = [
        {
            'gauge': '0xd8b712d29381748dB89c36BCa0138d7c75866ddF',
            'token': '0x090185f2135308BaD17527004364eBcC2D37e5F6',
        },
        {
            'gauge': '0x1cEBdB0856dd985fAe9b8fEa2262469360B8a3a6',
            'token': '0xD533a949740bb3306d119CC777fa900bA034cd52',
        },
        {
            'gauge': '0xDeFd8FdD20e0f34115C7018CCfb655796F6B2168',
            'token': '0xD533a949740bb3306d119CC777fa900bA034cd52',
        },
    ]
    ybribe = Contract(web3.ens.resolve('ybribe.ychad.eth'),owner=worker)
    voter = Contract(web3.ens.resolve('curve-voter.ychad.eth'),owner=worker)
    claims_to_make = 0
    for c in claims:
        gauge = c['gauge']
        token = c['token']
        if ybribe.active_period(gauge, token) + WEEK < chain.time():
            ybribe.add_reward_amount(gauge, token, 0, tx_params)
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
    print('Calling splitter....')
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
                send_alert(CHAT_IDS['WAVEY_ALERTS'], m, True)
            except Exception as e:
                transaction_failure(e)

def th_sweeper():
    print('Sweeping from TH....')
    f = open('sweep_tokens_list.json')
    try:
        sweep_tokens = json.load(f)
    except:
        # scripts.generate_token_data.generate_token_data(target_usd_value=TARGET_USD_VALUE)
        sweep_tokens = json.load(f)
    try:
        last_update = sweep_tokens['last_updated']
    except:
        last_update = 0
    # if time.time() - last_update > 60 * 60 * 24:
        # scripts.generate_token_data.generate_token_data(target_usd_value=TARGET_USD_VALUE)
    th = Contract('0xb634316E06cC0B358437CbadD4dC94F1D3a92B3b', owner=worker)
    calls, token_list, balance_list = ([] for i in range(3))
    # Use multicall to reduce http requests
    tkns = []
    for token_address in sweep_tokens:
        if token_address == 'last_updated':
            continue
        if token_address in ignore_tokens:
            continue
        # calls.append(
        #     Call(token_address, ['balanceOf(address)(uint256)', th.address], [[token_address, None]])
        # )
        print(f'BEFORE CALL.... {token_address}')
        tkns.append(ERC20(token_address, asynchronous=True))
        print(f'After CALL.')
    
    return_values = await_awaitable(asyncio.gather(*[token.balance_of(th.address, chain.height)  for token in tkns]))
    # return_values = Multicall(calls)()
    for i in range(0,len(return_values)):
        token_address = tkns[i]
        balance = return_values[i]
        if balance >= sweep_tokens[token_address]['threshold']:
            token_list.append(token_address)
            balance_list.append(balance)
    print(f'{len(token_list)}/{len(sweep_tokens)} tokens eligible for sweep',flush=True)
    if len(token_list) > 0:
        print(f'Sweeping...')
        syms = ""
        for t in token_list:
            print(t)
        try:
            tx = th.sweep(token_list, balance_list, tx_params)
            m = f'🧹 Sweep Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['SEASOLVER'], m, True)
        except Exception as e:
            transaction_failure(e)

def claim_warden_bribes():
    print('Claiming from Warden....')
    txn_params = {'max_fee':80e9, 'priority_fee':1e8}
    recipient = '0xF147b8125d2ef93FB6965Db97D6746952a133934'
    recipient = '0x527e80008D212E2891C737Ba8a2768a7337D7Fd2'
    url = f'https://claims.warden.vote/proof/crv/address/{recipient}'
    data = requests.get(url).json()
    distributor = Contract('0x3682518b529e4404fb05250f9ad590c3218e5f9f', owner=worker)
    for d in data:
        if d['questId'][:2] == 'd_':
            # Use Dark Quest distributor
            quest_id = int(d['questId'][2:len(d['questId'])])
            distributor = Contract('0xce6dc32252d85e2e955Bfd3b85660917F040a933', owner=worker)
        else:
            quest_id = int(d['questId'])
            distributor = Contract('0x3682518b529e4404fb05250f9ad590c3218e5f9f', owner=worker)
        try:
            tx = distributor.claim(
                quest_id,               # questID
                int(d['period']),       # period
                int(d['index']),        # index
                d['user'],              # account
                int(d['amount']),       # amount
                d['proofs'],            # proofs
                txn_params,             # txn params
            )
        except:
            pass

def transaction_failure(e):
    worker = accounts.at(AUTOMATION_EOA, force=True)
    print(e,flush=True)
    bal = worker.balance()
    msg = f'🤬 Unable to send transaction.\n\n🔗 [automation EOA](https://etherscan.io/address/0xA009Cf8B0eDddf58A3c32Be2D85859fA494b12e3)\n\nCurrent ETH balance available: {bal/10**18}'
    send_alert(CHAT_IDS['WAVEY_ALERTS'], msg, False)

def send_alert(chat_id, msg, success):
    bot.send_message(chat_id, msg, parse_mode="markdown", disable_web_page_preview = True)

def claim_prisma_hh():
    print('Claiming from HH....')
    claim_contract = Contract('0xa9b08B4CeEC1EF29EdEC7F9C94583270337D6416', owner=worker)
    voter = '0x90be6DFEa8C80c184C442a36e17cB2439AAE25a7'
    url = f'https://api.hiddenhand.finance/reward/0/{voter}'
    data = requests.get(url).json()['data']
    claims = []
    for d in data:
        if float(d['claimable']) > 0:
            metadata = d['claimMetadata']
            claim = (
                metadata['identifier'],
                voter,
                int(metadata['amount']),
                metadata['merkleProof']
            )
            claims.append(claim)

    if len(claims) > 0:
        tx = claim_contract.claim(claims, {'priority_fee':1e6})
        m = f'🌈🤖 Prisma Bribe Claim Detected!'
        m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
        send_alert(CHAT_IDS['YLOCKERS'], m, True)

def distribute_yprisma_fees():
    print('Distributing yPRISMA fees....')
    distributor = Contract('0x1D385BEEb7B325f4A5C0a9507FD8a1071B232E4c', owner=worker)
    if distributor.canClaim():
        tx = distributor.distributeFees()
        m = f'🌈🤖 Prisma Staker Yield Distributed!'
        m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
        send_alert(CHAT_IDS['YLOCKERS'], m, True)