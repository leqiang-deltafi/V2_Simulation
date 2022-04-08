from lib.lp_bots import DeltafiAMMLP
from .prototypes import AMM
from .price_data import Oracle

''' simple V2 implementation '''
class DeltafiAMM(AMM):
  def __init__(
    self, initial_reserve_A, initial_reserve_B, oracle: Oracle, fee_rate=0, 
    enable_external_exchange=False, enable_price_adjustment=False, enable_conf_interval=False):
    
    '''
    target reserve for calculating the A to B ratio only
    so we only care about the ratio
    it will be updated upon deposit and withdrawal
    '''
    self.target_reserve_A = initial_reserve_A
    self.target_reserve_B = initial_reserve_B

    ''' 
    A is USDC
    B is ETH
    '''
    self.balance_A = initial_reserve_A
    self.balance_B = initial_reserve_B
    self.share_A_supply = initial_reserve_A
    self.share_B_supply = initial_reserve_B

    self.oracle = oracle
    self.fee_rate = fee_rate

    '''
    In the simulation, we assume we are always do external exchange with current oracle price
    therefore, if we enable the external exchange, we are always able to keep the pool balanced and
    there is no need to adjust the price under unbalanced situation, so enable price adjustment does not
    make difference if 
    '''
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

  ''' implied price for how much A we can buy when selling 1 B '''
  def get_implied_price_B_for_A(self):
    price_B_selling_B = self.oracle.get_price() - self.get_conf_interval()
    price_modifier = self.target_reserve_B / self.target_reserve_A * self.balance_A / self.balance_B

    if self.enable_price_adjustment and price_modifier > 1:
      return price_B_selling_B

    result = price_B_selling_B * price_modifier
    return result*(1 - self.fee_rate)

  ''' implied price for how much B we can buy when selling 1 A '''
  def get_implied_price_A_for_B(self):
    price_A_selling_A = 1 / (self.oracle.get_price() + self.get_conf_interval())
    price_modifier = self.target_reserve_A / self.target_reserve_B * self.balance_B / self.balance_A

    if self.enable_price_adjustment and price_modifier > 1:
      return price_A_selling_A
    
    result = price_A_selling_A * price_modifier
    return result*(1 - self.fee_rate)

  ''' get how much token A can be bought with token B with price adjustment '''
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
      return token_A_output * (1 - self.fee_rate)
    
    if sell_B_to_target > 0:
      buy_A_to_target = sell_B_to_target * price_B_selling_B
      exp = price_B_selling_B * self.target_reserve_B / self.target_reserve_A
      buy_A_beyond_target = (self.balance_A - buy_A_to_target) * (1 - ((self.balance_B + sell_B_to_target) / (token_B_input + self.balance_B))**exp)

      return (buy_A_to_target + buy_A_beyond_target) * (1 - self.fee_rate)
    
    return self._get_swap_out_A_regular(token_B_input)

  ''' get how much token A can be bought with token B without price adjustment '''
  def _get_swap_out_A_regular(self, token_B_input):
    price_B_selling_B = self.oracle.get_price() - self.get_conf_interval()
    exp = price_B_selling_B * self.target_reserve_B / self.target_reserve_A
    result = self.balance_A * (1 - (self.balance_B / (token_B_input + self.balance_B))**exp)

    return result * (1 - self.fee_rate)

  def get_swap_out_A(self, token_B_input):
    if self.enable_price_adjustment is True:
      return self._get_swap_out_A_adjusted(token_B_input)
    return self._get_swap_out_A_regular(token_B_input)

  ''' get how much token B can be bought with token A with price adjustment '''
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

      return token_B_output*(1 - self.fee_rate)
    
    if sell_A_to_target > 0:
      buy_B_to_target = sell_A_to_target * price_A_selling_A
      exp = price_A_selling_A * self.target_reserve_A / self.target_reserve_B
      buy_B_beyond_target = (self.balance_B - buy_B_to_target) * (1 - ((self.balance_A + sell_A_to_target) / (token_A_input + self.balance_A))**exp)

      return (buy_B_to_target + buy_B_beyond_target) * (1 - self.fee_rate)

    return self._get_swap_out_B_regular(token_A_input)

  ''' get how much token B can be bought with token A without price adjustment '''
  def _get_swap_out_B_regular(self, token_A_input):
    price_A_selling_A = 1 / (self.oracle.get_price() + self.get_conf_interval())
    exp = price_A_selling_A * self.target_reserve_A / self.target_reserve_B
    result = self.balance_B * (1 - (self.balance_A / (token_A_input + self.balance_A))**exp)

    return result*(1 - self.fee_rate)

  def get_swap_out_B(self, token_A_input):
    if self.enable_price_adjustment is True:
      return self._get_swap_out_B_adjusted(token_A_input)
    return self._get_swap_out_B_regular(token_A_input)

  ''' do the swap: sell A for B '''
  def swap_A_for_B(self, token_A_input):
    implied_price = self.get_implied_price_A_for_B()

    token_B_output = self.get_swap_out_B(token_A_input)
    self.balance_A += token_A_input
    self.balance_B -= token_B_output

    actual_price = token_B_output / token_A_input

    return token_A_input, abs(implied_price - actual_price) / implied_price

  ''' do the swap: sell B for A '''
  def swap_B_for_A(self, token_B_input):
    # print("swap_B_for_A before", str(self.balance_A), str(self.balance_B))
    implied_price = self.get_implied_price_B_for_A()

    token_A_output = self.get_swap_out_A(token_B_input)
    self.balance_A -= token_A_output
    self.balance_B += token_B_input
    actual_price = token_A_output / token_B_input

    return token_A_output, abs(implied_price - actual_price) / implied_price
  
  ''' using current oracle price, get current_tvl/initial_tvl '''
  def get_tvl_ratio_to_initial_state(self):

    current_tvl = self.balance_A + self.balance_B * self.oracle.get_price()
    initial_tvl = self.target_reserve_A + self.target_reserve_B * self.oracle.get_price()
    
    return current_tvl / initial_tvl

  ''' 
  do the deposit
  input token B amount, calculate token A amount that comes together with token B
  get share A and share B amount
  '''
  def lp_deposit(self, token_B_amount):

    token_A_amount = token_B_amount * self.oracle.get_price()
    
    current_tvl = self.balance_A + self.balance_B * self.oracle.get_price()
    initial_tvl = self.target_reserve_A + self.target_reserve_B * self.oracle.get_price()

    normalized_balance_A = self.target_reserve_A * (current_tvl / initial_tvl)
    normalized_balance_B = self.target_reserve_B * (current_tvl / initial_tvl)
    
    share_A = self.share_A_supply * (token_A_amount / normalized_balance_A)
    share_B = self.share_B_supply * (token_B_amount / normalized_balance_B)

    self.balance_A += token_A_amount
    self.balance_B += token_B_amount
    self.share_A_supply += share_A
    self.share_B_supply += share_B
    self.target_reserve_A = normalized_balance_A + token_A_amount
    self.target_reserve_B = normalized_balance_B + token_B_amount

    return share_A, share_B, token_A_amount
  
  '''
  do the withdraw
  input share A and share B amount, calculate how much token A and token B to come out
  there is no restriction between share A and share B here
  but in reality, we will record the LP's total share and only allow LP
  the withdraw same percentage of his share A and share B
  '''
  def lp_withdraw(self, share_A, share_B):
  
    selected_balance_A = self.balance_A
    selected_balance_B = self.balance_B

    current_A_to_B_ratio = self.balance_A / self.balance_B
    target_A_to_B_ratio = self.target_reserve_A / self.target_reserve_B

    if current_A_to_B_ratio < target_A_to_B_ratio:
      selected_balance_B = self.balance_A * (self.target_reserve_B / self.target_reserve_A)
    else:
      selected_balance_A = self.balance_B * (self.target_reserve_A / self.target_reserve_B)

    delta_A = self.balance_A - selected_balance_A
    delta_B = self.balance_B - selected_balance_B

    token_A_amount = selected_balance_A * (share_A / self.share_A_supply)
    token_B_amount = selected_balance_B * (share_B / self.share_B_supply)

    share_tvl_ratio = (token_A_amount + token_B_amount * self.oracle.get_price()) / (selected_balance_A + selected_balance_B * self.oracle.get_price())

    token_A_amount += delta_A * share_tvl_ratio
    token_B_amount += delta_B * share_tvl_ratio

    selected_balance_A -= selected_balance_A * (share_A / self.share_A_supply)
    selected_balance_B -= selected_balance_B * (share_B / self.share_B_supply)

    self.share_A_supply -= share_A
    self.share_B_supply -= share_B

    self.balance_A -= token_A_amount
    self.balance_B -= token_B_amount

    self.target_reserve_A = selected_balance_A
    self.target_reserve_B = selected_balance_B

    return token_A_amount, token_B_amount
  
  ''' get the lp bot used for deposit/withdraw simulation '''
  def get_lp_bot(self, max_deposit_record, min_holding_cycles, deposit_prob, withdraw_prob):
    return DeltafiAMMLP(
      self, oracle=self.oracle, max_deposit_record=max_deposit_record, min_holding_cycles=min_holding_cycles, 
      deposit_prob=deposit_prob, withdraw_prob=withdraw_prob)
