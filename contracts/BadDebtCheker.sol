pragma solidity ^0.8.19;

interface IDualOracle {
    function getPrices() external view returns (bool _isBadData, uint256 _priceLow, uint256 _priceHigh);
    function decimals() external view returns (uint);
}

interface IFraxlendPair {
    function exchangeRateInfo() external view returns (ExchangeRateInfo memory);
    function totalBorrow() external view returns (VaultAccount memory);
    function totalCollateral() external view returns (uint);
    struct ExchangeRateInfo {
        address oracle;
        uint32 maxOracleDeviation; // % of larger number, 1e5 precision
        uint184 lastTimestamp;
        uint256 lowExchangeRate;
        uint256 highExchangeRate;
    }
    struct VaultAccount {
        uint128 amount; // Total amount, analogous to market cap
        uint128 shares; // Total shares, analogous to shares outstanding
    }
}

interface IVault {
    function maxWithdraw(address _owner) external view returns (uint);
    function totalAssets() external view returns (uint);
}

contract BadDebtChecker {

    function isPairSolvent(IFraxlendPair _pair) external view returns (bool) {
        return getPairCollateralValue(_pair) > getPairBorrowValue(_pair);
    }

    function isLiquid(address _pair, uint _amount) external view returns (bool) {
        return isLiquid(msg.sender, _pair, _amount);
    }

    function isLiquid(address _user, address _pair, uint _amount) public view returns (bool) {
        return IVault(_pair).maxWithdraw(_user) > _amount;
    }

    function getPairCollateralValue(IFraxlendPair _pair) public view returns (uint) {
        IDualOracle oracle = IDualOracle(_pair.exchangeRateInfo().oracle);
        (, uint256 _priceLow,) = oracle.getPrices();
        return _pair.totalCollateral() * 10 ** oracle.decimals() / _priceLow;
    }

    function getPairBorrowValue(IFraxlendPair _pair) public view returns (uint) {
        return _pair.totalBorrow().amount;
    }
}

