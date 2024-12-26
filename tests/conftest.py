from brownie import accounts, ZERO_ADDRESS, BadDebtChecker
from eth_abi import encode
from eth_utils import to_checksum_address, to_hex
import pytest
from eth_abi import encode
from eth_utils import to_checksum_address, to_hex

@pytest.fixture(scope="session", autouse=True)
def user():
    return accounts[0]

@pytest.fixture(scope="session", autouse=True)
def dev():
    return accounts[9]

@pytest.fixture(scope="session", autouse=True)
def checker(dev):
    return dev.deploy(BadDebtChecker)