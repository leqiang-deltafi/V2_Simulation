from .prototypes import AMM
from .price_data import Oracle

# simple V2 implementation
# TODO: add deposit and withdraw after discussion
class DeltafiAMM(AMM):
  def __init__(
    self, initial_reserve_A, initial_reserve_B, oracle: Oracle, fee_rate=0, 
    enable_external_exchange=False, enable_price_adjustment=False, enable_conf_interval=False):
    
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

    assert(not (enable_external_exchange and enable_price_adjustment))
    self.enable_external_exchange = enable_external_exchange
    self.enable_price_adjustment = enable_price_adjustment
    self.enable_conf_interval = enable_conf_interval

  def get_name(self):
    name = "deltafi V2"
    if self.enable_external_exchange is True:
      name += " + external exchange"
    if self.enable_price_adjustment is True:
      name += " + price adjustment"
    if self.enable_conf_interval is True:
      name += " + confidence interval"

    if self.fee_rate > 0:
      name += ",fee rate=" + str(self.fee_rate*100) + "%"

    return name

  def get_balance_A(self):
    return self.balance_A

  def get_balance_B(self):
    return self.balance_B

  def get_conf_interval(self):
    if self.enable_conf_interval is True:
      return self.oracle.get_conf_interval()
    return 0

  # implied price for how much A we can buy when selling 1 B
  def get_implied_price_B_for_A(self):
    price_B_selling_B = self.oracle.get_price() - self.get_conf_interval()
    price_modifier = self.target_reserve_B / self.target_reserve_A * self.balance_A / self.balance_B

    if self.enable_price_adjustment and price_modifier > 1:
      return price_B_selling_B

    result = price_B_selling_B * price_modifier
    return result*(1 - self.fee_rate)

  # implied price for how much B we can buy when selling 1 A
  def get_implied_price_A_for_B(self):
    price_A_selling_A = 1 / (self.oracle.get_price() + self.get_conf_interval())
    price_modifier = self.target_reserve_A / self.target_reserve_B * self.balance_B / self.balance_A

    if self.enable_price_adjustment and price_modifier > 1:
      return price_A_selling_A
    
    result = price_A_selling_A * price_modifier
    return result*(1 - self.fee_rate)

  def _get_swap_out_A_adjusted(self, token_B_input):
    price_B_selling_B = self.oracle.get_price() - self.get_conf_interval()

    current_value_in_A = self.balance_A + self.balance_B * price_B_selling_B
    initial_value_in_A = self.target_reserve_A + self.target_reserve_B * price_B_selling_B

    target_A = self.target_reserve_A * (current_value_in_A / initial_value_in_A)
    target_B = self.target_reserve_B * (current_value_in_A / initial_value_in_A)

    sell_B_to_target = target_B - self.balance_B

    if token_B_input < sell_B_to_target:
      token_A_output = token_B_input * price_B_selling_B
      assert(self.balance_A - token_A_output >= target_A)
      # print("_get_swap_out_A_adjusted_0", token_B_input, token_A_output, self._get_swap_out_A_regular(token_B_input))
      return token_A_output * (1 - self.fee_rate)
    
    if sell_B_to_target > 0:
      buy_A_to_target = sell_B_to_target * price_B_selling_B
      exp = price_B_selling_B * self.target_reserve_B / self.target_reserve_A
      buy_A_beyond_target = (self.balance_A - buy_A_to_target) * (1 - ((self.balance_B + sell_B_to_target) / (token_B_input + self.balance_B))**exp)

      # print("_get_swap_out_A_adjusted_1", token_B_input, buy_A_to_target + buy_A_beyond_target, self._get_swap_out_A_regular(token_B_input))
      return (buy_A_to_target + buy_A_beyond_target) * (1 - self.fee_rate)
    
    return self._get_swap_out_A_regular(token_B_input)

  def _get_swap_out_A_regular(self, token_B_input):
    price_B_selling_B = self.oracle.get_price() - self.get_conf_interval()
    exp = price_B_selling_B * self.target_reserve_B / self.target_reserve_A
    result = self.balance_A * (1 - (self.balance_B / (token_B_input + self.balance_B))**exp)

    return result * (1 - self.fee_rate)

  def get_swap_out_A(self, token_B_input):
    if self.enable_price_adjustment is True:
      return self._get_swap_out_A_adjusted(token_B_input)
    return self._get_swap_out_A_regular(token_B_input)

  def _get_swap_out_B_adjusted(self, token_A_input):
    price_A_selling_A = 1 / (self.oracle.get_price() + self.get_conf_interval())
    current_value_in_B = self.balance_A * price_A_selling_A + self.balance_B
    initial_value_in_B = self.target_reserve_A * price_A_selling_A + self.target_reserve_B

    target_A = self.target_reserve_A * (current_value_in_B / initial_value_in_B)
    target_B = self.target_reserve_B * (current_value_in_B / initial_value_in_B)

    sell_A_to_target = target_A - self.balance_A

    if token_A_input < sell_A_to_target:
      token_B_output = token_A_input * price_A_selling_A
      assert(self.balance_B - token_B_output >= target_B)

      # print("_get_swap_out_B_adjusted_0", token_A_input, token_B_output, self._get_swap_out_B_regular(token_A_input))
      return token_B_output*(1 - self.fee_rate)
    
    if sell_A_to_target > 0:
      buy_B_to_target = sell_A_to_target * price_A_selling_A
      exp = price_A_selling_A * self.target_reserve_A / self.target_reserve_B
      buy_B_beyond_target = (self.balance_B - buy_B_to_target) * (1 - ((self.balance_A + sell_A_to_target) / (token_A_input + self.balance_A))**exp)

      # print("_get_swap_out_B_adjusted_1", token_A_input, buy_B_to_target + buy_B_beyond_target, self._get_swap_out_B_regular(token_A_input))
      return (buy_B_to_target + buy_B_beyond_target) * (1 - self.fee_rate)

    return self._get_swap_out_B_regular(token_A_input)

  # how much B we can actually get if we sell token_A_input amount of A
  def _get_swap_out_B_regular(self, token_A_input):
    price_A_selling_A = 1 / (self.oracle.get_price() + self.get_conf_interval())
    exp = price_A_selling_A * self.target_reserve_A / self.target_reserve_B
    result = self.balance_B * (1 - (self.balance_A / (token_A_input + self.balance_A))**exp)

    # print("get_swap_out_B", str(token_A_input), str(result))
    return result*(1 - self.fee_rate)

  def get_swap_out_B(self, token_A_input):
    if self.enable_price_adjustment is True:
      return self._get_swap_out_B_adjusted(token_A_input)
    return self._get_swap_out_B_regular(token_A_input)

  # do the swap: sell A for B
  def swap_A_for_B(self, token_A_input):
    # print("swap_A_for_B before", str(self.balance_A), str(self.balance_B))
    implied_price = self.get_implied_price_A_for_B()

    token_B_output = self.get_swap_out_B(token_A_input)
    self.balance_A += token_A_input
    self.balance_B -= token_B_output

    actual_price = token_B_output / token_A_input

    # print("swap_A_for_B after", str(self.balance_A), str(self.balance_B))
    return token_A_input, abs(implied_price - actual_price) / implied_price

  # do the swap: sell B for A
  def swap_B_for_A(self, token_B_input):
    # print("swap_B_for_A before", str(self.balance_A), str(self.balance_B))
    implied_price = self.get_implied_price_B_for_A()

    token_A_output = self.get_swap_out_A(token_B_input)
    self.balance_A -= token_A_output
    self.balance_B += token_B_input
    actual_price = token_A_output / token_B_input

    # print("swap_B_for_A after", str(self.balance_A), str(self.balance_B))

    return token_A_output, abs(implied_price - actual_price) / implied_price
  
  def get_tvl_ratio_to_initial_state(self):

    current_tvl = self.balance_A + self.balance_B * self.oracle.get_price()
    initial_tvl = self.target_reserve_A + self.target_reserve_B * self.oracle.get_price()
    
    # print("get_tvl_ratio_to_initial_state", str(current_tvl), str(initial_tvl))
    return current_tvl / initial_tvl
