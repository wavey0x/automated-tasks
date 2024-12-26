import time, re, json, requests, datetime, time, os, telebot, scripts.generate_token_data, logging
from multicall import Call, Multicall
from multicall.utils import await_awaitable
from y import ERC20
import asyncio

from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from brownie import (Contract, accounts, ZERO_ADDRESS, chain, web3, interface, ZERO_ADDRESS)

class TroveOperation:
    OPEN = 0
    CLOSE = 1
    ADJUST = 2

    @staticmethod
    def to_string(operation):
        if operation == TroveOperation.OPEN:
            return "Opened"
        elif operation == TroveOperation.CLOSE:
            return "Closed"
        elif operation == TroveOperation.ADJUST:
            return "Adjusted"
        return "Unknown"

load_dotenv(find_dotenv())
DAY = 60 * 60 * 24
WEEK = DAY * 7
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

env = 'PROD' if os.environ.get('ENV') == 'PROD' else 'DEV'
bot = telebot.TeleBot(telegram_bot_key)
CHAT_IDS = {
    "WAVEY_ALERTS": "-789090497",
    "YCRV": "-1001653990357",
    "SEASOLVER": "-1001516144118",
    "YBRIBE": "-1001862925311",
    "VEYFI": "-1001558128423",
    "YLOCKERS": "-1001697527660",
    "PRISMA_REVOKE": "-1001992546130",
    "MCKINSEY": "-1002118993173",
}

ignore_tokens = [
    '0x836A808d4828586A69364065A1e064609F5078c7', # pETH
]

ADDRESSES = {
    'YEARN_CURVE_VOTER': '0xF147b8125d2ef93FB6965Db97D6746952a133934',
    'YTRADES': '0xC001d00d425Fa92C4F840baA8f1e0c27c4297a0B',
    'SPLITTER': '0x527e80008D212E2891C737Ba8a2768a7337D7Fd2',
    'YBRIBE': '0x03dFdBcD4056E2F92251c7B07423E1a33a7D3F6d',
    'YCHAD': '0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52',
    'TREASURY': '0x93A62dA5a14C80f265DAbC077fCEE437B1a0Efde',
    'CURVE_VE': '0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2',

}

def main():
    # prisma_approvals()
    ybs_alerts()
    th_sweeper()
    # stg_harvest()
    claim_votemarket()
    # claim_bribes()
    # yearn_fed()
    # bribe_splitter()
    # temple_split()
    # ycrv_donator()
    claim_quest_bribes()
    claim_prisma_hh()
    deposit_ybs_rewards()
    new_ycrv_splitter()
    prisma_tm_alerts()
    
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
    print('Claiming from vote market....', flush=True)
    buffer_time = 60 * 60 * 6
    week_start = int(chain.time() / WEEK) * WEEK
    if week_start + buffer_time > chain.time() - 500:
        return # Only proceed if we've waited the buffer time
    voter = Contract(ADDRESSES['YEARN_CURVE_VOTER'],owner=worker)
    markets = [
        '0x0000000895cB182E6f983eb4D8b4E0Aa0B31Ae4c',
        '0x000000073D065Fc33a3050C2d0E19C393a5699ba',
    ]
    helper = Contract('0xD0108D6bC206eCFE38E496F0ed95fD9E9F96beE0')
    for m in markets:
        ids_from_helper = list(helper.getClaimableIds(m, voter))
        if len(ids_from_helper) > 0:
            market = Contract(m, owner=worker)
            tx = market.claimAllFor(voter, ids_from_helper, tx_params)
            m = f'🤖 {len(ids_from_helper)} Votemarket Bribe Claim(s) Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['YLOCKERS'], m, True)

def claim_bribes():
    print('Claiming from ybribe....', flush=True)
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
    ybribe = Contract(ADDRESSES['YBRIBE'],owner=worker)
    voter = Contract(ADDRESSES['YEARN_CURVE_VOTER'],owner=worker)
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
    ytrades = accounts.at(ADDRESSES['YTRADES'], force=True)
    bribe_splitter = Contract(ADDRESSES['SPLITTER'], owner=ADDRESSES['YCHAD'])
    bribe_splitter.setOperator(AUTOMATION_EOA, True)
    spell = Contract('0x090185f2135308BaD17527004364eBcC2D37e5F6',owner=ytrades)
    spell.transfer(bribe_splitter,spell.balanceOf(ytrades))
    treasury = accounts.at(ADDRESSES['TREASURY'], force=True)
    crv = Contract('0xD533a949740bb3306d119CC777fa900bA034cd52',owner=treasury)
    crv.transfer(bribe_splitter,crv.balanceOf(treasury))
    ychad = accounts.at(ADDRESSES['YCHAD'], force=True)
    usdt = Contract('0xdAC17F958D2ee523a2206206994597C13D831ec7', owner=ychad)
    th = '0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b'
    usdt.transfer(th, 100e6)
    # sweeper = Contract('0xCca030157c6378eD2C18b46e194f10e9Ad01fa8d', owner=worker)
    # tx = sweeper.sweep([usdt.address], [100e6], txn_params)
    
def bribe_splitter():
    bribe_splitter = Contract(ADDRESSES['SPLITTER'], owner=worker)
    ybribe = Contract(ADDRESSES['YBRIBE'])
    voter = Contract(ADDRESSES['YEARN_CURVE_VOTER'])
    f = open('splitter.json')
    data = json.load(f)
    st = Contract('0x27B5739e22ad9033bcBf192059122d163b60349D')
    ycrv = Contract(st.token())
    ybs = Contract('0xE9A115b77A1057C918F997c32663FdcE24FB873f')
    ybs_balance = ycrv.balanceOf(ybs) + ycrv.balanceOf(st)
    for token_address in data:
        token = Contract(token_address)
        gauge = data[token_address]['gauge']
        should_claim = data[token_address]['should_claim']
        split_threshold = data[token_address]['split_threshold']
        balance = token.balanceOf(bribe_splitter)
        symbol = token.symbol()
        # print(f'{symbol} balance: {balance/10**token.decimals()} threshold: {split_threshold/10**token.decimals()}',flush=True)
        if balance > split_threshold:
            if should_claim and ybribe.claimable(voter, gauge, token_address) < 1e18:
                should_claim = False # Override if claim not worth it
            try:
                tx = bribe_splitter.bribesSplitWithManualStBalance(token_address, gauge, ybs_balance, should_claim, tx_params)
                m = f'🖖 {symbol} Split Detected!'
                m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
                send_alert(CHAT_IDS['WAVEY_ALERTS'], m, True)
            except Exception as e:
                transaction_failure(e)

def th_sweeper():
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
        tkns.append(ERC20(token_address, asynchronous=True))
    
    return_values = await_awaitable(asyncio.gather(*[token.balance_of(th.address, chain.height)  for token in tkns]))
    # return_values = Multicall(calls)()
    for i in range(0,len(return_values)):
        token_address = tkns[i]
        balance = return_values[i]
        if balance >= sweep_tokens[token_address]['threshold']:
            token_list.append(token_address)
            balance_list.append(balance)
    print(f'Sweeper {len(token_list)}/{len(sweep_tokens)} tokens eligible for sweep',flush=True)
    if len(token_list) > 0:
        try:
            tx = th.sweep(token_list, balance_list, tx_params)
            m = f'🧹 Sweep Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['SEASOLVER'], m, True)
        except Exception as e:
            transaction_failure(e)
    else:
        return

def claim_quest_bribes():
    print('Claiming from Quest....',flush=True)
    txn_params = {'max_fee':40e9, 'priority_fee':1e5}
    recipient = '0xF147b8125d2ef93FB6965Db97D6746952a133934'
    recipient = '0x527e80008D212E2891C737Ba8a2768a7337D7Fd2'
    # recipient = '0xb911Fcce8D5AFCEc73E072653107260bb23C1eE8'
    recipient = '0xb911Fcce8D5AFCEc73E072653107260bb23C1eE8'
    url = f'https://claims.warden.vote/proof/crv/address/{recipient}'
    url = f'https://api.paladin.vote/quest/v2/copilot/claims/{recipient}'
    url = f'https://api.paladin.vote/quest/v3/copilot/claims/{recipient}'
    data = requests.get(url).json()['claims']
    claim_data = []
    for d in data:
        distributor = Contract(d['distributor'], owner=worker)
        quest_id = int(d['questId'])
        period = int(d['period'])
        index = int(d['index'])

        if distributor.isClaimed(quest_id,period,index):
            continue

        if env != 'PROD':
            print(f'Attempting claim on quest ID: {quest_id}')

        claim_data.append((
            quest_id,
            period,
            index,
            d['amount'],
            d['proofs']
        ))
    
    num_claims = len(claim_data)
    if num_claims > 0:
        try:
            tx = distributor.multiClaim(
                d['user'],              # account
                claim_data
            )
            m = f'{num_claims} Quest Bribe Claim(s) Detected!'
            m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
            send_alert(CHAT_IDS['YLOCKERS'], m, True)
        except Exception as e:
            transaction_failure(e)
 
def transaction_failure(e):
    worker = accounts.at(AUTOMATION_EOA, force=True)
    print(e,flush=True)
    bal = worker.balance()
    msg = f'🤬 Unable to send transaction.\n\n🔗 [automation EOA](https://etherscan.io/address/0xA009Cf8B0eDddf58A3c32Be2D85859fA494b12e3)\n\nCurrent ETH balance available: {bal/10**18}'
    send_alert(CHAT_IDS['WAVEY_ALERTS'], msg, False)

def send_alert(chat_id, msg, success):
    bot.send_message(chat_id, msg, parse_mode="markdown", disable_web_page_preview = True)

def claim_prisma_hh():
    claim_contract = Contract('0xa9b08B4CeEC1EF29EdEC7F9C94583270337D6416', owner=worker)
    voter = '0x90be6DFEa8C80c184C442a36e17cB2439AAE25a7'
    fee_receiver = '0x76DF88Aa8711822472Cb40Ed8c972A461A20ecdc'
    url = f'https://api.hiddenhand.finance/reward/0/{fee_receiver}'
    data = requests.get(url).json()['data']
    claims = []
    for d in data:
        if float(d['claimable']) > 0:
            print('Claiming from HH....')
            metadata = d['claimMetadata']
            claim = (
                metadata['identifier'],
                fee_receiver,
                int(metadata['amount']),
                metadata['merkleProof']
            )
            claims.append(claim)

    if len(claims) > 0:
        tx = claim_contract.claim(claims, tx_params)
        m = f'🌈🤖 Prisma Bribe Claim Detected!'
        m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
        send_alert(CHAT_IDS['YLOCKERS'], m, True)

def deposit_ybs_rewards():
    txn_params = {'priority_fee':1e6}
    # distributor = Contract('0x1D385BEEb7B325f4A5C0a9507FD8a1071B232E4c', owner=worker)
    yprisma_distributor = Contract('0x5aA86e9558F7701A90f343D90e0bC55AEb0046Df', owner=worker)
    ycrv_receiver = Contract('0x642a16A7885d7a8b9353E2a4B68834f31389dC2c', owner=worker)
    if yprisma_distributor.canClaim():
        print('Depositing yPRISMA fees....')
        tx = yprisma_distributor.distributeFees(txn_params)
        m = f'🌈🤖 Prisma Yield Deposited!'
        m += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
        send_alert(CHAT_IDS['YLOCKERS'], m, True)

    reward_token = Contract(ycrv_receiver.REWARD_TOKEN())
    balance = reward_token.balanceOf(ycrv_receiver)
    THRESHOLD = 100e18
    if balance > THRESHOLD:
        print('Depositing yCRV rewards....')
        tx = ycrv_receiver.depositRewards(txn_params)
        m = f'🌀🤖 yCRV Yield Deposited!'
        m += f'\n\nAmount: {balance/1e18:,.2f}\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
        send_alert(CHAT_IDS['YLOCKERS'], m, True)


def prisma_approvals():
    # Check if the file exists
    users = ["0x57d7e9853072ddf1e288fa4d7ee52412bfbb8347", "0x539dfe636d8ea473f093d3dc4881a80cc5fc7dff", "0x728d66a885376d1ddf0809f4254085f171b157bd", "0x14b30b46ec4fa1a993806bd5dda4195c5a82353e", "0x0424e057c2d0bc7e58c75975aaf38bf1e598cd49", "0xd0917ac1daacc35cc5aa3b5b987171723aa7230b", "0xb0f094c9e85a0ee7b89214a3a67efbc131022cc0", "0x603642f696d77a1feda2e982d87ac7f517c1f058", "0xee9536e8aea9384f1a8ddf655a7e9ee4579a160f", "0x20eadfcaf91bd98674ff8fc341d148e1731576a4", "0x1b004189e64d5b2f71d5be554470e6c49e10123b", "0x2239ac202240074b006a0cd2c201284a284dfe21", "0x4ebfcf3707e5bbc9f96d88da57ee47d1ec49820c", "0x83f6fe95067e24af601b1b822430c72c0098d208", "0x3056b7039deb4347ca9ab2abd7b5785fcdcc0ebf", "0xfc3871a15aeba37883911a825ec78b7676adebce", "0x16f570e93fdbc3a4865b7740deb052ee94d87e15", "0x85d545937db8d3bbc45288914da7286442e9a2c7", "0x262c199d993b09a9d5d35fbb8be312a8ddb48016", "0x38f2944e482a050942e5fb1652af4690017cd141", "0xcd493a43d9fb5a1b2b7d5739cc0c674c798dffe5", "0xc47fae56f3702737b69ed615950c01217ec5c7c8", "0xcbfdffd7a2819a47fcd07dfa8bcb8a5deacc9ea8", "0x844850092711b0ebbb75f6fa8b65561d4811d61d", "0x21c8f9fc8ea09a859b514a5607eac80d23f6d6fb", "0xfda1215797d29414e588b2e62fc390ee2949aaaa", "0x19562df3e7fd2ae7af4e6bd288b04c2c90405212", "0x0a9aca1ae6b4e60931a1a8ef034580074bff763c", "0xd996073019c74b2fb94ead236e32032405bc027c", "0xe0042d684fe6bfa4d897082f97b41532aa39640c", "0x46d35cb6bab2a106dae7b201be149bd4ed534348", "0xdbd5e81eb31a210459f5d4c057651ffce5f742aa", "0x1b8a9f9f5a1d9cb1c28d9120f9c2bd073ccfac04", "0x192820ce84fa9eb457fb228c386fe0ed22f7e33c", "0x93e45360f7e5b0b85d8e65dae9fa1a6f2af56819", "0x477baede70cb2e7723e010600df84674a4baafaf", "0x7bfee91193d9df2ac0bfe90191d40f23c773c060", "0x2d1ef4acf4cae6a38950971aaaa15f88d9b3f165", "0x4148310fe4544e82f176570c6c7b649290a90e17", "0x7ab5386c78c73b10d04c470315948a2983ad7b68", "0x787b24cecefec7af515f096b29d13d4d2fe9918d", "0xebc48e8db0d9203db04512ec4a8030cf2a43c384", "0xc9782d4880de737d48c75153b51e36a7b2475974", "0xe513b2b8745a83ebdc1b42b5ce70d4900b5981c7"]
    users = [web3.toChecksumAddress(u) for u in users]
    file_path = 'prisma_approvals.json'
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
            except:
                data = {}
                data['vulnerable'] = users
                data['vulnerable_count'] = 44
                data['last_run'] = chain.time()
    else:
        data = {}
        data['vulnerable_count'] = 44
        data['vulnerable'] = users
        data['last_run'] = chain.time()
        with open(file_path, 'w') as file:
            json.dump(data, file)

    vuln = []
    attackers = [
        "0x4148310fe4544e82f176570C6c7B649290a90E17", 
        "0x1b8A9F9F5a1d9cB1C28D9120F9c2bD073ccfAC04", 
        "0xD996073019c74B2fB94eAD236e32032405bC027c"
    ]
    borrower_ops = Contract('0x72c590349535AD52e6953744cb2A36B409542719')
    zap = '0xcC7218100da61441905e0c327749972e3CBee9EE'
    for user in users:
        user = web3.toChecksumAddress(user)
        approved = borrower_ops.isApprovedDelegate(user, zap)
        if approved and user not in attackers:
            vuln.append(user)
            # print(user, approved)
    
    count = len(vuln)
    print(f'{count}/{len(users)}')

    if 'vulnerable' in data:
        vulnerable = data['vulnerable']
    
    if len(data['vulnerable']) != count:
        changed = [v for v in vulnerable if v not in vuln]
        changed_str = '\n- '.join([f'`{item}` ${get_collateral_value(item):,.0f}' for item in changed])
        vuln_str = '\n- '.join([f'`{item}` ${get_collateral_value(item):,.0f}' for item in vuln])
        msg = f'🌈 Detected {len(changed)} new revokes since last run:\n\n- {changed_str} \n\n ⚠️ {len(vuln)} live approvals remain. \n\n- {vuln_str}'
        chat = 'PRISMA_REVOKE' if env != 'dev' else 'WAVEY_ALERTS'
        if os.environ.get('ENVIRONMENT2') == 'PROD':
            bot.send_message(CHAT_IDS[chat], msg, parse_mode="markdown", disable_web_page_preview = True)
        data['vulnerable_count'] = count
        data['vulnerable'] = vuln
        data['last_run'] = chain.time()
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4) 

def get_collateral_value(user):
    factory = Contract('0x70b66E20766b775B2E9cE5B718bbD285Af59b7E1')
    price_oracle = Contract('0xC105CeAcAeD23cad3E9607666FEF0b773BC86aac')
    tms = []
    for i in range(0, factory.troveManagerCount()):
        tms.append(factory.troveManagers(i))
    collat_values = {}
    for tm in tms:
        tm = Contract(tm)
        collat = tm.collateralToken()
        amt = tm.getTroveCollAndDebt(user)['coll']/1e18
        if amt > 0:
            price = price_oracle.fetchPrice.call(collat) / 1e18
            collat_values[collat] = collat_values.get(collat, 0) + (price * amt)
    
    return sum(collat_values.values())

def ybs_alerts():
    THRESHOLD = 500_000
    registry = Contract('0x262be1d31d0754399d8d5dc63B99c22146E9f738')
    tokens = [
        '0xFCc5c47bE19d06BF83eB04298b026F81069ff65b', # yCRV
    ]

    block = chain.height
    from_block = block - 10_000
    to_block = block
    data = {}
    ts = chain.time()
    dt = datetime.utcfromtimestamp(ts).strftime("%m/%d/%Y, %H:%M:%S")
    file_path = 'local_data.json'
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                from_block = data['last_run_block']+1
            except:
                print('Error reading local data file.')
    data['last_run_block'] = block
    data['last_run_ts'] = ts
    data['last_run_dt'] = dt

    for token in tokens:
        token = Contract(token)
        deployment = registry.deployments(token)
        ybs = Contract(deployment['yearnBoostedStaker'])
        rewards = Contract(deployment['rewardDistributor'])
        utils = Contract(deployment['utilities'])
        logs = ybs.events.Staked.get_logs(fromBlock=from_block, toBlock=to_block)
        logs += ybs.events.Unstaked.get_logs(fromBlock=from_block, toBlock=to_block)
        for log in logs:
            account = log.args['account']
            txn_hash = log.transactionHash.hex()
            amount = log.args['amount'] / 1e18
            if amount < THRESHOLD:
                continue
            ts = ybs.totalSupply() / 1e18
            global_weight = ybs.getGlobalWeight() / 1e18
            avg_multiplier = global_weight / ts
            abbr, link, markdown = abbreviate_address(account)
            event = log['event']
            msg = f'🌈 Large YBS {event[:-1]} detected\n\n{markdown} {event} {amount:,.0f} {token.symbol()}\n\n 🔗 [View on Etherscan](https://etherscan.io/tx/{txn_hash})'
            if env == 'PROD':
                bot.send_message(CHAT_IDS['MCKINSEY'], msg, parse_mode="markdown", disable_web_page_preview = True)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4) 

def abbreviate_address(address):
    KNOWN_ADDRESSES = {

    }
    link = f'https://etherscan.io/address/{address}'
    if address in KNOWN_ADDRESSES:
        abbr = KNOWN_ADDRESSES[address]
        markdown = f'[{abbr}]({link})'
    else:
        abbr = f'{address[0:5]}...{address[-4:]}'
        markdown = f'[{abbr}]({link})'
    return abbr, link, markdown

def lock_crv():
    txn_params = {'priority_fee':1e6}
    voter = Contract(ADDRESSES['YEARN_CURVE_VOTER'], owner=worker)
    proxy = Contract(voter.strategy(), owner=worker)
    crv = Contract(voter.crv())

    if crv.balanceOf(voter) > 100e18:
        proxy.lock(txn_params)

def new_ycrv_splitter():
    THRESHOLD = 4_000 # Minimum amount of crvUSD worth splitting
    ts = time.time()
    txn_params = {'priority_fee':1e6}
    split_target_ts = int(ts / WEEK) * WEEK + (DAY * 2) # Saturday 00:00 UTC
    fee_burner = Contract('0xb911Fcce8D5AFCEc73E072653107260bb23C1eE8')
    splitter = Contract('0x05Fc8174050f0A41dEB7e562187911d45cd5e401', owner=worker)
    proxy = Contract('0x78eDcb307AC1d1F8F5Fd070B377A6e69C8dcFC34')
    crvusd_balance = Contract(proxy.crvUSD()).balanceOf(fee_burner) / 1e18

    if (
        ts > split_target_ts and
        (
            proxy.canClaim() or
            crvusd_balance >= THRESHOLD
        )
    ):
        msg = f'✂️ yCRV Split Executed \n'
        splits = splitter.getSplits()
        admin_fee_splits = splits['adminFeeSplits']
        vote_incentive_splits = splits['voteIncentiveSplits']
        tx = splitter.executeSplit(txn_params)
        if 'AdminFeeSplit' in tx.events:
            amts = tx.events['AdminFeeSplit'][0]
            msg += f'\n👔 Admin Fee Splits'
            msg += f'\nUser: {amts["ybs"]/1e18:,.2f} | {admin_fee_splits[0]/1e16:,.2f}%'
            msg += f'\nTreasury: {amts["treasury"]/1e18:,.2f} | {admin_fee_splits[1]/1e16:,.2f}%'
            msg += f'\nRemainders: {amts["remainder"]/1e18:,.2f} | {admin_fee_splits[2]/1e16:,.2f}%'
        if 'VoteIncentiveSplit' in tx.events:
            amts = tx.events['VoteIncentiveSplit'][0]
            msg += f'\n\n 🗳️  Vote Incentive Splits'
            total =  amts["ybs"]/1e18 / (vote_incentive_splits[0] / 1e18)
            remainders_amount = total * vote_incentive_splits[2] / 1e18
            msg += f'\nUser: {amts["ybs"]/1e18:,.2f} | {vote_incentive_splits[0]/1e16:,.2f}%'
            msg += f'\nTreasury: {amts["treasury"]/1e18:,.2f} | {vote_incentive_splits[1]/1e16:,.2f}%'
            msg += f'\nRemainders: {remainders_amount:,.2f} | {vote_incentive_splits[2]/1e16:,.2f}%'
        msg += f'\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{tx.txid})'
        bot.send_message(CHAT_IDS['MCKINSEY'], msg, parse_mode="markdown", disable_web_page_preview = True)


def prisma_tm_alerts():
    print('Checking for Prisma Trove updates....')
    from web3._utils.events import construct_event_topic_set
    managers = get_tvl_by_manager()
    total_tvl = sum(managers.values())
    bo = Contract('0x72c590349535AD52e6953744cb2A36B409542719')
    prisma_bo = ['0x72c590349535AD52e6953744cb2A36B409542719','0xeCabcF7d41Ca644f87B25704cF77E3011D9a70a1']
    last_run_block = get_last_run_block()
    last_run_block = last_run_block if last_run_block > 0 else 21289076# 21489076
    contract = web3.eth.contract(bo.address, abi=bo.abi)
    topics = construct_event_topic_set(
        contract.events.TroveUpdated().abi, 
        web3.codec,
        {}
    )
    logs = web3.eth.get_logs(
        { 'topics': topics, 'fromBlock': last_run_block, 'toBlock': chain.height }
    )
    events = contract.events.TroveUpdated().process_receipt({'logs': logs})
    print(f'{len(events)} events detected')
    for event in events:
        if event.address not in prisma_bo:
            continue
        borrower = event.args['_borrower']
        block_number = event.blockNumber
        txn_hash = event.transactionHash.hex()
        collateral = event.args['_coll']
        debt = event.args['_debt']
        operation = TroveOperation.to_string(event.args['operation'])
        print(
            borrower, 
            collateral/1e18, 
            debt/1e18,
            operation
        )
        msg = f'🌈 Prisma Repayment Detected\n\n[{borrower[:5]}...{borrower[-3:]}](https://etherscan.io/address/{borrower}) {operation} their trove \nUser collat: {collateral/1e18:,.2f} \nUser debt: {debt/1e18:,.2f}'
        msg += f'\n\n💰 TVL Remaining: ${total_tvl:,.2f}\n\n🔗 [View on Etherscan](https://etherscan.io/tx/{txn_hash})'
        send_alert(CHAT_IDS['WAVEY_ALERTS'], msg, True)

def get_tvl_by_manager():
    factories = [Contract('0x70b66E20766b775B2E9cE5B718bbD285Af59b7E1'), Contract('0xDb2222735e926f3a18D7d1D0CFeEf095A66Aea2A')]
    managers = {}
    for factory in factories:
        count = factory.troveManagerCount() 
        for i in range (0, count):
            tm = factory.troveManagers(i)
            if tm == ZERO_ADDRESS:
                break
            managers[tm] = Contract(tm).getTotalActiveDebt()/1e18
    return managers

def get_last_run_block():
    file_path = 'local_data.json'
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                return data['last_run_block']
            except:
                print('Error reading local data file.')
    return 0