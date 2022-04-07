
from abc import abstractclassmethod
from .price_data import Oracle

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
  @abstractclassmethod
  def lp_deposit(self, token_B_amount):
    raise NotImplementedError
  @abstractclassmethod
  def lp_withdraw(self, *args) -> tuple([float, float]):
    raise NotImplementedError
  @abstractclassmethod
  def get_lp_bot(self):
    raise NotImplementedError


class TradingBot():
  @abstractclassmethod
  def maybe_execute_trade(self, amm: AMM):
    raise NotImplementedError

class LPBot():
  def __init__(
    self, amm: AMM, oracle: Oracle, 
    max_deposit_record=1000, min_holding_cycles=10000, deposit_prob=1, withdraw_prob=0.05) -> None:
      self.amm = amm 
      self.oracle = oracle
      self.max_deposit_record = max_deposit_record
      self.min_holding_cycles = min_holding_cycles
      self.deposit_prob = deposit_prob
      self.withdraw_prob = withdraw_prob
      self.result_list: list[float] = []

      self.max_deposit_B_amount = 10
  
  @abstractclassmethod
  def update_record(self, cycle):
    raise NotImplementedError
  
  @abstractclassmethod
  def get_result(self) -> list[float]:
    raise NotImplementedError