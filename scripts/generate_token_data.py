import time, re, json, requests, datetime, time, os, telebot
from multicall import Call, Multicall
from dotenv import load_dotenv, find_dotenv
from brownie import (Contract, accounts, ZERO_ADDRESS, chain, web3, interface, ZERO_ADDRESS)
from brownie.exceptions import BrownieEnvironmentWarning, BrownieCompilerWarning
import warnings
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore", BrownieEnvironmentWarning)
warnings.simplefilter("ignore", BrownieCompilerWarning)

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


def generate_token_data(TARGET_USD_VALUE):
    tokens = get_tokens()
    oracle = Contract("0x83d95e0D5f402511dB06817Aff3f9eA88224B030")
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

def get_tokens():
    list = [
        "0xfcc5c47be19d06bf83eb04298b026f81069ff65b", "0xff709449528b6fb6b88f557f7d93dece33bca78d", 
        "0x3175df0976dfa876431c2e9ee6bc45b65d3473cc", "0x111111517e4929d3dcbdfa7cce55d30d4b6bc4d6",  
        "0x1a7e4e63778b4f12a199c062f3efdd288afcbce8", "0x62b9c7356a2dc64a1969e19c23e4f579f9810aa7", 
        "0x9ae380f0272e2162340a5bb646c354271c0f5cfc", "0xc55126051b22ebb829d00368f4b12bde432de5da", 
        "0xbe9895146f7af43049ca1c1ae358b0541ea49704", "0x3432b6a60d23ca0dfca7761b7ab56459d9c964d0", 
        "0xf05e58fcea29ab4da01a495140b349f8410ba904", "0xfeef77d3f69374f66429c91d732a244f074bdf74",
        "0x320623b8e4ff03373931769a31fc52a4e78b5d70", "0x2b591e99afe9f32eaa6214f7b7629768c40eeb39", 
        "0x8d6cebd76f18e1558d4db88138e2defb3909fad6", "0x9e32b13ce7f2e80a01932b42553652e053d6ed8e", 
        "0xd1b5651e55d4ceed36251c61c50c889b36f6abb5", "0x0f71b8de197a1c84d31de0f1fa7926c365f052b3", 
        "0x3aada3e213abf8529606924d8d1c55cbdc70bf74", "0x9813037ee2218799597d83d4a5b6f3b6778218d9", 
        "0xd084944d3c05cd115c09d072b9f44ba3e0e45921", "0xcafe001067cdef266afb7eb5a286dcfd277f3de5", 
        "0xc0c293ce456ff0ed870add98a0828dd4d2903dbf", "0x6f80310ca7f2c654691d1383149fa1a57d8ab1f8", 
        "0xb6ca7399b4f9ca56fc27cbff44f4d2e4eef1fc81", "0x3d3d35bb9bec23b06ca00fe472b50e7a4c692c30", 
        "0x29059568bb40344487d62f7450e78b8e6c74e0e5", "0xfb7b4564402e5500db5bb6d63ae671302777c75a", 
        "0x31d4eb09a216e181ec8a43ce79226a487d6f0ba9", "0x3b6831c0077a1e44ed0a21841c3bc4dc11bce833", 
        "0x0f5d2fb29fb7d3cfee444a200298f468908cc942", "0x4a220e6096b25eadb88358cb44068a3248254675", 
        "0x33349b282065b0284d756f0577fb39c158f935e6", "0x579cea1889991f68acc35ff5c3dd0621ff29b0c9", 
        "0x69af81e73a73b40adf4f3d4223cd9b1ece623074", "0x892a6f9df0147e5f079b0993f486f9aca3c87881", 
        "0x3845badade8e6dff049820680d1f14bd3903a5d0", "0x5cac718a3ae330d361e39244bf9e67ab17514ce8", 
        "0x8a854288a5976036a725879164ca3e91d30c6a1b", "0xabe580e7ee158da464b51ee1a83ac0289622e6be", 
        "0x5ca135cb8527d76e932f34b5145575f9d8cbe08e", "0x767fe9edc9e0df98e07454847909b5e959d7ca0e", 
        "0xf411903cbc70a74d22900a5de66a2dda66507255", "0x48c3399719b582dd63eb5aadf12a40b4c3f52fa2", 
        "0xa13a9247ea42d743238089903570127dda72fe44", "0x402f878bdd1f5c66fdaf0fababcf74741b68ac36", 
        "0x4edcb2b46377530bc18bb4d2c7fe46a992c73e10", "0x6967299e9f3d5312740aa61dee6e9ea658958e31", 
        "0x6468e79a80c0eab0f9a2b574c8d5bc374af59414", "0x5b3240b6be3e7487d61cd1afdfc7fe4fa1d81e64", 
        "0x23b608675a2b2fb1890d3abbd85c5775c51691d5", "0xab846fb6c81370327e784ae7cbb6d6a6af6ff4bf",
        "0x01597e397605bf280674bf292623460b4204c375"
    ]
    new_list = [web3.toChecksumAddress(l) for l in list]
    tokens = {
        "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e": "YFI",
        "0x0d438f3b5175bebc262bf23753c1e53d03432bde": "wNXM",
        "0x0d8775f648430679a709e98d2b0cb6250d2887ef": "BAT",
        "0x1f573d6fb3f13d689ff844b4ce37794d79a7ff1c": "BNT",
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": "WBTC",
        "0x2ba592f78db6436527729929aaf6c908497cb200": "CREAM",
        "0x408e41876cccdc0f92210600ef50372656052a38": "REN",
        "0x4fabb145d64652a948d72533023f6e7a623c7c53": "BUSD",
        "0x514910771af9ca656af840dff83e8264ecf986ca": "LINK",
        "0x6810e776880c02933d47db1b9fc05908e5386b96": "GNO",
        "0x8e870d67f660d95d5be530380d0ec0bd388289e1": "USDP",
        "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2": "MKR",
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
        "0xba100000625a3754423978a60c9317c58a424e3d": "BAL",
        "0xba11d00c5f74255f56a5e366f4f77f5a186d7f55": "BAND",
        "0xbbbbca6a901c926f240b89eacb641d8aec7aeafd": "LRC",
        "0xc00e94cb662c3520282e6f5717214004a7f26888": "COMP",
        "0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f": "SNX",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
        "0xd46ba6d942050d489dbd938a2c909a5d5039a161": "AMPL",
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
        "0xdb25f211ab05b1c97d595516f45794528a807ad8": "EURS",
        "0xe41d2489571d322189246dafa5ebde1f4699f498": "ZRX",
        "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d": "renBTC",
        "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0": "MATIC",
        "0x6b175474e89094c44da98b954eedeac495271d0f": "DAI",
        "0x57ab1ec28d129707052df4df418d58a2d46d5f51": "sUSD",
        "0x0000000000085d4780b73119b644ae5ecd22b376": "TUSD",
        "0x056fd409e1d7a124bd7017459dfea2f387b6d5cd": "GUSD",
        "0x8daebade922df735c38c80c7ebd708af50815faa": "tBTC",
        "0x45804880de22913dafe09f4980848ece6ecbaf78": "PAXG",
        "0xfca59cd816ab1ead66534d82bc21e7515ce441cf": "RARI",
        "0xd533a949740bb3306d119cc777fa900ba034cd52": "CRV",
        "0x674c6ad92fd080e4004b2312b45f796a192d27a0": "USDN",
        "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2": "SUSHI",
        "0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b": "DPI",
        "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": "UNI",
        "0x429881672b9ae42b8eba0e26cd9c73711b891ca5": "PICKLE",
        "0xa0246c9032bc3a600820415ae600c6388619a14d": "FARM",
        "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": "AAVE",
        "0xbc396689893d065f41bc2c6ecbee5e0085233447": "PERP",
        "0xe2f2a5c287993345a840db3b0845fbc70f5935a5": "mUSD",
        "0x584bc13c7d411c00c01a62e8019472de68768430": "HEGIC",
        "0xff20817765cb7f73d4bde2e66e067e58d11095c2": "AMP",
        "0x0391d2021f89dc339f60fff84546ea23e337750f": "BOND",
        "0x1ceb5cb57c4d4e2b2433641b95dd330a33185a44": "KP3R",
        "0x0954906da0bf32d5479e25f46056d22f08464cab": "INDEX",
        "0x8888801af4d980682e47f1a9036e589479e835c5": "MPH",
        "0x3472a5a71965499acd81997a54bba8d852c6e53d": "BADGER",
        "0xc944e90c64b2c07662a292be6244bdf05cda44a7": "GRT",
        "0x5a98fcbea516cf06857215779fd812ca3bef1b32": "LDO",
        "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": "stETH",
        "0x111111111117dc0aa78b770fa6a738034120c302": "1INCH",
        "0xc770eefad204b5180df6a14ee197d99d808ee52d": "FOX",
        "0xffffffff2ba8f66d4e51811c5190992176930278": "COMBO",
        "0x853d955acef822db058eb8505911ed77f175b99e": "FRAX",
        "0x73968b9a57c6e53d41345fd57a6e6ae27d6cdb2f": "SDT",
        "0x8290333cef9e6d528dd5618fb97a76f268f3edd4": "ANKR",
        "0x4e15361fd6b4bb609fa63c81a2be19d873717870": "FTM",
        "0x3832d2f059e55934220881f831be501d180671a7": "renDOGE",
        "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce": "SHIB",
        "0x875773784af8135ea0ef43b5a374aad105c5d39e": "IDLE",
        "0x03ab458634910aad20ef5f1c8ee96f1d6ac54919": "RAI",
        "0xf99d58e463a2e07e5692127302c20a191861b4d6": "ANY",
        "0x126c121f99e1e211df2e5f8de2d96fa36647c855": "DEGEN",
        "0xdbdb4d16eda451d0503b854cf79d55697f90c8df": "ALCX",
        "0x41d5d79431a913c4ae7d69a668ecdfe5ff9dfb68": "INV",
        "0x956f47f50a910163d8bf957cf5846d573e7f87ca": "FEI",
        "0x5f98805a4e8be255a32880fdec7f6728c6568ba0": "LUSD",
        "0xf16e81dce15b08f326220742020379b855b87df9": "ICE",
        "0x2d94aa3e47d9d5024503ca8491fce9a2fb4da198": "BANK",
        "0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b": "CVX",
        "0xde30da39c46104798bb5aa3fe8b9e0e1f348163f": "GTC",
        "0xbc6da0fe9ad5f3b0d58160288917aa56653660e9": "alUSD",
        "0xc581b735a1688071a1746c968e0798d642ede491": "EURT",
        "0x92d6c1e31e14520e676a687f0a93788b716beff5": "DYDX",
        "0x15b7c0c907e4c6b9adaaaabc300c08991d6cea05": "GEL",
        "0x99d8a9c45b2eca8864373a26d1459e3dff1e17f3": "MIM",
        "0x090185f2135308bad17527004364ebcc2d37e5f6": "SPELL",
        "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0": "wstETH",
        "0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6": "sBTC",
        "0x5e74c9036fb86bd7ecdcb084a0673efc32ea31cb": "sETH",
        "0xc18360217d8f7ab5e7c516566761ea12ce7f9d72": "ENS",
        "0xae78736cd615f374d3085123a210448e74fc6393": "rETH",
        "0xcfeaead4947f0705a14ec42ac3d44129e1ef3ed5": "NOTE",
        "0x47110d43175f7f2c2425e7d15792acc5817eb44f": "GMI",
        "0x31429d1856ad1377a8a0079410b297e1a9e214c2": "ANGLE",
        "0xf57e7e7c23978c3caec3c3548e3d615c346e79ff": "IMX",
        "0x2e9d63788249371f1dfc918a52f8d799f4a38c94": "TOKE",
        "0x0f2d719407fdbeff09d87557abb7232601fd9f29": "SYN",
        "0x4d224452801aced8b2f0aebe155379bb5d594381": "APE",
        "0xaf5191b0de278c7286d6c7cc6ab6bb8a73ba2cd6": "STG",
        "0xdef1ca1fb7fbcdc777520aa7f396b4e015f497ab": "COW",
        "0xc5102fe9359fd9a28f877a67e36b0f050d81a3cc": "HOP",
        "0x6c3f90f043a72fa612cbac8115ee7e52bde6e490": "3crv",
        "0x2af1df3ab0ab157e1e2ad8f88a7d04fbea0c7dc6": "BED",
        "0xd33526068d116ce69f19a9ee46f0bd304f21a51f": "RPL",
        "0xf1dc500fde233a4055e25e5bbf516372bc4f6871": "SDL",
        "0x865377367054516e17014ccded1e7d814edc9ce4": "DOLA",
        "0x5afe3855358e112b5647b952709e6165e1c1eeee": "SAFE"
    }
    for t in tokens:
        new_list.append(t)

    helper = Contract("0x52CbF68959e082565e7fd4bBb23D9Ccfb8C8C057")
    vaults = helper.getVaults()
    for v in vaults:
        new_list.append(v)
    assert False
    return new_list

if __name__ == '__main__':
    # test1.py executed as script
    # do something
    generate_token_data()