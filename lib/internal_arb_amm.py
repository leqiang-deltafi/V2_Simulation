from abc import abstractclassmethod
from .prototypes import AMM
from .deltafi_amm import DeltafiAMM
from .uniswap_amm import UniswapAMM

from lib.price_data import Oracle
from .prototypes import AMM
import math

''' parent class for uniswap/deltafi amm with internal arb '''
class InternalArbAMM(AMM):

  def __init__(self, initial_balance_A, initial_balance_B, oracle: Oracle, arb_pool_ratio=0.1, arb_rebalance_ratio=1) -> None:
    self.arb_balance_A = initial_balance_A * arb_pool_ratio
    self.arb_balance_B = initial_balance_B * arb_pool_ratio
    self.child_amm = AMM()

    ''' initial arb pool ratio of the whole pool '''
    self.arb_pool_ratio = arb_pool_ratio
    ''' 
    if this ratio is 1, each time the rebalance will be targeted at getting the pool fully rebalanced
    if it is less than 1, the rebalancing function will limit the amount of token for rebalancing
    '''
    self.arb_rebalance_ratio = arb_rebalance_ratio

    self.oracle = oracle
    self.target_balance_A = initial_balance_A
    self.target_balance_B = initial_balance_B

  def get_balance_A(self):
    return self.child_amm.get_balance_A()

  def get_balance_B(self):
    return self.child_amm.get_balance_B()

  @abstractclassmethod
  def rebalance(self):
    raise NotImplementedError

  def _simulate_rebalance_with_func(self, func, *args):
    balance_A = self.child_amm.balance_A
    balance_B = self.child_amm.balance_B 
    arb_balance_A = self.arb_balance_A
    arb_balance_B = self.arb_balance_B

    self.rebalance()
    result = func(*args)

    self.child_amm.balance_A = balance_A
    self.child_amm.balance_B = balance_B
    self.arb_balance_A = arb_balance_A
    self.arb_balance_B = arb_balance_B

    return result

  def get_implied_price_B_for_A(self) -> float:
    return self._simulate_rebalance_with_func(self.child_amm.get_implied_price_B_for_A)
  
  def get_implied_price_A_for_B(self) -> float:
    return self._simulate_rebalance_with_func(self.child_amm.get_implied_price_A_for_B)
  
  def get_swap_out_A(self, token_B_input, do_simulation=True):
    if do_simulation is True:
      return self._simulate_rebalance_with_func(self.child_amm.get_swap_out_A, token_B_input)
    return self.child_amm.get_swap_out_A(token_B_input)
  
  def get_swap_out_B(self, token_A_input, do_simulation=True):
    if do_simulation is True:
      return self._simulate_rebalance_with_func(self.child_amm.get_swap_out_B, token_A_input)
    return self.child_amm.get_swap_out_B(token_A_input)
  
  def swap_A_for_B(self, token_A_input):
    self.rebalance()
    return self.child_amm.swap_A_for_B(token_A_input)

  def swap_B_for_A(self, token_B_input):
    self.rebalance()
    return self.child_amm.swap_B_for_A(token_B_input)

  def get_tvl_ratio_to_initial_state(self):
    total_A = self.arb_balance_A + self.child_amm.balance_A 
    total_B = self.arb_balance_B + self.child_amm.balance_B 

    current_tvl = total_A + total_B * self.oracle.get_price()
    initial_tvl = self.target_balance_A + self.target_balance_B * self.oracle.get_price()

    return current_tvl / initial_tvl

class DeltafiInternalArbAMM(InternalArbAMM):
  def __init__(self, initial_balance_A, initial_balance_B, oracle: Oracle, arb_pool_ratio=0.1, arb_rebalance_ratio=1, fee_rate=0, enable_external_exchange=False):
    super().__init__(initial_balance_A, initial_balance_B, oracle, arb_pool_ratio, arb_rebalance_ratio)
    self.child_amm: DeltafiAMM = DeltafiAMM(
      self.target_balance_A - self.arb_balance_A, self.target_balance_B - self.arb_balance_B, 
      oracle=oracle, fee_rate=fee_rate, enable_external_exchange=False, enable_price_adjustment=False
    )

    self.enable_external_exchange = enable_external_exchange
  
  def get_name(self):
    return "Deltafi V2 + internal arb pool"

  @staticmethod
  def get_optimal_trade(target_ratio_A_to_B, balance_A, balance_B, oracle_price):
    P = 1 / oracle_price
    sell_A_amount = (((balance_B * target_ratio_A_to_B) * balance_A**(P*target_ratio_A_to_B))**(1/((P*target_ratio_A_to_B) + 1))) - balance_A
    sell_B_amount = (((balance_A / target_ratio_A_to_B) * balance_B**(oracle_price/target_ratio_A_to_B))**(1/((oracle_price/target_ratio_A_to_B) + 1))) - balance_B
    return sell_A_amount, sell_B_amount

  def rebalance(self):
    oracle_price = self.oracle.get_price()
    target_ratio_A_to_B = self.target_balance_A / self.target_balance_B
    delta_A, delta_B = self.get_optimal_trade(target_ratio_A_to_B, self.child_amm.get_balance_A(), self.child_amm.get_balance_B(), oracle_price)

    if delta_A > 0:
      arb_sell_A = max(0, min(delta_A*self.arb_rebalance_ratio, self.arb_balance_A))
      arb_buy_B = self.get_swap_out_B(arb_sell_A, do_simulation=False)

      self.child_amm.balance_A += arb_sell_A
      self.child_amm.balance_B -= arb_buy_B
      self.arb_balance_A -= arb_sell_A
      self.arb_balance_B += arb_buy_B

    elif delta_B > 0:
      arb_sell_B = max(0, min(delta_B*self.arb_rebalance_ratio, self.arb_balance_B))
      arb_buy_A = self.get_swap_out_A(arb_sell_B, do_simulation=False)

      self.child_amm.balance_A -= arb_buy_A
      self.child_amm.balance_B += arb_sell_B
      self.arb_balance_A += arb_buy_A
      self.arb_balance_B -= arb_sell_B


class UniswapInternalArbAMM(InternalArbAMM):
  def __init__(self, initial_balance_A, initial_balance_B, oracle: Oracle, arb_pool_ratio=0.1, arb_rebalance_ratio=1, fee_rate=0, enable_external_exchange=False):
    super().__init__(initial_balance_A, initial_balance_B, oracle, arb_pool_ratio, arb_rebalance_ratio)
    self.enable_external_exchange = enable_external_exchange
    self.child_amm: UniswapAMM = UniswapAMM(
      initial_balance_A - self.arb_balance_A, initial_balance_B - self.arb_balance_B, 
      oracle=oracle, fee_rate=fee_rate
    )
  
  def get_name(self):
    return "uniswap + internal pool"

  def rebalance(self):
    oracle_price = self.oracle.get_price()
    current_k = self.child_amm.balance_A * self.child_amm.balance_B
    target_B = math.sqrt(current_k / oracle_price)
    target_A = target_B * oracle_price

    delta_A = target_A - self.child_amm.balance_A
    delta_B = target_B - self.child_amm.balance_B

    if delta_A > 0:
      arb_sell_A = max(0, min(delta_A, self.arb_balance_A))
      old_balance_B = self.child_amm.balance_B
      self.child_amm.balance_A += arb_sell_A
      self.child_amm.balance_B = current_k / self.child_amm.balance_A
      self.arb_balance_A -= arb_sell_A
      self.arb_balance_B += old_balance_B - self.child_amm.balance_B
    elif delta_B > 0:
      arb_sell_B = max(0, min(delta_B, self.arb_balance_B))
      old_balance_A = self.child_amm.balance_A
      self.child_amm.balance_B += arb_sell_B
      self.child_amm.balance_A = current_k / self.child_amm.balance_B
      self.arb_balance_A += old_balance_A - self.child_amm.balance_A
      self.arb_balance_B -= arb_sell_B
