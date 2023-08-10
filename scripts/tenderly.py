from brownie import web3, ZERO_ADDRESS, Contract, chain, accounts, web3
from dotenv import dotenv_values
import requests

def tenderly_fork():
    env_vars = dotenv_values()
    TENDERLY_ACCESS_KEY = env_vars['TENDERLY_ACCESS_KEY']
    TENDERLY_USER = env_vars['TENDERLY_USER']
    TENDERLY_PROJECT = env_vars['TENDERLY_PROJECT']
    url = f'https://api.tenderly.co/api/v1/account/{TENDERLY_USER}/project/{TENDERLY_PROJECT}/fork'
    headers = {
        'X-Access-Key': str(TENDERLY_ACCESS_KEY)
    }
    data = {
      'network_id': '1',
    }
    
    response = requests.post(url, json=data, headers=headers)
    fork_id = response.json()["simulation_fork"]["id"]
    fork_rpc_url = f"https://rpc.tenderly.co/fork/{fork_id}"
    tenderly_provider = web3.HTTPProvider(fork_rpc_url, {"timeout": 600})
    web3.provider = tenderly_provider
    print(f"https://dashboard.tenderly.co/{TENDERLY_USER}/{TENDERLY_PROJECT}/fork/{fork_id}")