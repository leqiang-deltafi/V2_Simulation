from .prototypes import AMM

# class that implement uniswap for comparison
# TODO: add deposit and withdraw after discussion
class UniswapAMM(AMM):
  def __init__(self, initial_reserve_A, initial_reserve_B, oracle, fee_rate=0):
    self.initial_reserve_A = initial_reserve_A
    self.initial_reserve_B = initial_reserve_B
    self.oracle = oracle
    # initial reserves
    # token A is USDC, token B is ETH
    # price is number of USDC to buy a ETH
    self.balance_A = initial_reserve_A
    self.balance_B = initial_reserve_B
    self.K = initial_reserve_A * initial_reserve_B
    self.fee_rate = fee_rate

  def get_name(self):
    name = "Uniswap"
    if self.fee_rate > 0:
      name += ",fee rate=" + str(self.fee_rate*100) + "%"
    return name

  def get_balance_A(self):
    return self.balance_A

  def get_balance_B(self):
    return self.balance_B

  def get_implied_price_B_for_A(self):
    return (self.balance_A / self.balance_B) * (1 - self.fee_rate)
  
  def get_implied_price_A_for_B(self):
    return (self.balance_B / self.balance_A) * (1 - self.fee_rate)

  def get_swap_out_A(self, token_B_input):
    k = self.balance_A * self.balance_B
    token_A_output = self.balance_A - k / (self.balance_B + token_B_input)
    return token_A_output*(1 - self.fee_rate)

  def get_swap_out_B(self, token_A_input):
    k = self.balance_A * self.balance_B
    token_B_output = self.balance_B - k / (self.balance_A + token_A_input)
    return token_B_output*(1 - self.fee_rate)

  def swap_A_for_B(self, token_A_input):
    implied_price = self.get_implied_price_A_for_B()

    token_B_output = self.get_swap_out_B(token_A_input)
    self.balance_A += token_A_input
    self.balance_B -= token_B_output

    actual_price = token_B_output / token_A_input
    return token_A_input, abs(implied_price - actual_price) / implied_price

  def swap_B_for_A(self, token_B_input):
    implied_price = self.get_implied_price_B_for_A()

    token_A_output = self.get_swap_out_A(token_B_input)
    self.balance_A -= token_A_output
    self.balance_B += token_B_input

    actual_price = token_A_output / token_B_input
    return token_A_output, abs(implied_price - actual_price) / implied_price
  
  def get_tvl_ratio_to_initial_state(self):
    current_tvl = self.balance_A + self.balance_B * self.oracle.get_price()
    initial_tvl = self.initial_reserve_A + self.initial_reserve_B * self.oracle.get_price()

    return current_tvl / initial_tvl