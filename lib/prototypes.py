
from abc import abstractclassmethod

# virtual class for all amm types
class AMM():
    @abstractclassmethod
    def get_name(self):
        raise NotImplementedError
    @abstractclassmethod
    def get_balance_A(self):
        raise NotImplementedError
    def get_balance_B(self):
        raise NotImplementedError
    # implied price: how much B we can get from spending 1 A
    @abstractclassmethod
    def get_implied_price_A_for_B(self) -> float:
        raise NotImplementedError
    # implied price: how much A we can get from spending 1 B
    def get_implied_price_B_for_A(self) -> float:
        raise NotImplementedError
    @abstractclassmethod
    def get_swap_out_A(self, token_B_input: float):
        raise NotImplementedError
    @abstractclassmethod
    def get_swap_out_B(self, token_A_input: float):
        raise NotImplementedError
    @abstractclassmethod
    def swap_A_for_B(self, token_A_input):
        raise NotImplementedError
    @abstractclassmethod
    def swap_B_for_A(self, token_A_input):
        raise NotImplementedError
    @abstractclassmethod
    def get_tvl_ratio_to_initial_state(self):
        raise NotImplementedError

class TradingBot():
    @abstractclassmethod
    def maybe_execute_trade(self, amm: AMM):
        raise NotImplementedError