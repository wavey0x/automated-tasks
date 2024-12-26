import brownie
from brownie import chain, Contract
import pytest

def test_ops(dev, checker):
    pair = '0x78bB3aEC3d855431bd9289fD98dA13F9ebB7ef15'
    borrow_value = checker.getPairBorrowValue(pair)/1e18
    collat_value = checker.getPairCollateralValue(pair)/1e18
    checker.isPairSolvent(pair)
    assert False