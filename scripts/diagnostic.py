from web3 import HTTPProvider
from brownie import chain, web3, network

rpcs = [
    'http://192.168.1.102:8545', # wavey home node

    'https://eth:kcdWXdqrw3mM@erigon.yearn.science', # banteg
    
    'https://crebsy.yrpc.xyz/eth/854e20206e05f5b020a31426cebec92bb99ca38d4c688e719258f05e3c73eafb',
    'https://node.dyrpc.network/eth/854e20206e05f5b020a31426cebec92bb99ca38d4c688e719258f05e3c73eafb',

    'https://crebsy.yrpc.xyz/eth/f949c925f0326d98b40f50a03687523b36613465b9ad81b7800352d3053ebbfd',
    'https://node.dyrpc.network/eth/f949c925f0326d98b40f50a03687523b36613465b9ad81b7800352d3053ebbfd',

    'https://crebsy.yrpc.xyz/eth/d91f7c0376de89685f6c9576909cd82c655304b2d3475b2c31ce8c7824b54156',
    'https://node.dyrpc.network/eth/d91f7c0376de89685f6c9576909cd82c655304b2d3475b2c31ce8c7824b54156',
]

def main():
    for rpc in rpcs:
        network.web3.disconnect()
        network.web3.connect(rpc,timeout=300)
        emoji = '✅' if network.web3.isConnected() else '❌'
        height = 0
        try:
            height = chain.height
        except:
            pass
        print(rpc, emoji, height)