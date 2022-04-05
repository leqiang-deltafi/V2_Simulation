from prototypes import AMM
from price_data import Oracle

# simple V2 implementation
# TODO: add deposit and withdraw after discussion
class DeltafiAMM(AMM):
  def __init__(self, initial_reserve_A, initial_reserve_B, oracle: Oracle, fee_rate=0):
    
    # target reserve for calculating the A to B ratio only
    # it will be updated upon deposit and withdrawal
    self.target_reserve_A = initial_reserve_A
    self.target_reserve_B = initial_reserve_B

    # A is USDC
    # B is ETH
    self.balance_A = initial_reserve_A
    self.balance_B = initial_reserve_B

    self.oracle = oracle
    self.fee_rate = fee_rate
  
  # implied price for how much A we can buy when selling 1 B
  def get_implied_price_B_for_A(self):
    price_B_selling_B = self.oracle.get_price() - self.oracle.get_conf_interval()
    result = price_B_selling_B * self.target_reserve_B / self.target_reserve_A * self.balance_A / self.balance_B
    return result*(1 - self.fee_rate)

  # implied price for how much B we can buy when selling 1 A
  def get_implied_price_A_for_B(self):
    price_A_selling_A = 1 / (self.oracle.get_price() + self.oracle.get_conf_interval())
    result = price_A_selling_A * self.target_reserve_A / self.target_reserve_B * self.balance_B / self.balance_A
    return result*(1 - self.fee_rate)

  # how much A we can actually get if we sell token_B_input amout of B
  def get_swap_out_A(self, token_B_input):
    price_B_selling_B = self.oracle.get_price() - self.oracle.get_conf_interval()
    exp = price_B_selling_B * self.initial_reserve_B / self.initial_reserve_A
    result = self.balance_A * (1 - (self.balance_B / (token_B_input + self.balance_B))**exp)

    return result*(1 - self.fee_rate)

  # how much B we can actually get if we sell token_A_input amount of A
  def get_swap_out_B(self, token_A_input):
    price_A_selling_A = 1 / (self.oracle.get_price() + self.oracle.get_conf_interval())
    exp = price_A_selling_A * self.initial_reserve_A / self.initial_reserve_B
    result = self.balance_B * (1 - (self.balance_A / (token_A_input + self.balance_A))**exp)

    return result*(1 - self.fee_rate)

  # do the swap: sell A for B
  def swap_A_for_B(self, token_A_input):
    implied_price = self.get_implied_price_A_for_B()

    token_B_output = self.get_swap_out_B(token_A_input, do_simulation=False)
    self.balance_A += token_A_input
    self.balance_B -= token_B_output

    actual_price = token_B_output / token_A_input

    return token_A_input, abs(implied_price - actual_price) / implied_price

  # do the swap: sell B for A
  def swap_B_for_A(self, token_B_input):
    implied_price = self.get_implied_price_B_for_A()

    token_A_output = self.get_swap_out_A(token_B_input, do_simulation=False)
    self.balance_A -= token_A_output
    self.balance_B += token_B_input
    actual_price = token_A_output / token_B_input

    return token_A_output, abs(implied_price - actual_price) / implied_price
  
  def get_tvl_ratio_to_initial_state(self):
    total_A = self.balance_A + self.arb_balance_A
    total_B = self.balance_B + self.arb_balance_B

    current_tvl = total_A + total_B * self.oracle.get_price()
    initial_tvl = self.target_reserve_A + self.target_reserve_B * self.oracle.get_price()
    
    return current_tvl / initial_tvl