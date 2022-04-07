import random
from .prototypes import AMM, LPBot
from .price_data import Oracle

class UniswapLPBot(LPBot):
  def __init__(
    self, amm: AMM, oracle: Oracle, 
    max_deposit_record=1, min_holding_cycles=10000, deposit_prob=1, withdraw_prob=0.05
  ) -> None:
      super().__init__(amm, oracle, max_deposit_record, min_holding_cycles, deposit_prob, withdraw_prob)
      # (share, deposit_A_amount, deposit_B_amount, deposit_cycle)
      self.deposit_record: list[tuple([float, float, float, int])] = []

  def _remove_record_idx(self, idx):
    assert(idx < len(self.deposit_record))
    self.deposit_record[idx] = self.deposit_record[-1]
    self.deposit_record.pop()

  def update_record(self, cycle):
    record_removal_idx = []
    for i in range(len(self.deposit_record)):
      share, deposit_A_amount, deposit_B_amount, deposit_cycle = self.deposit_record[i]
      if (cycle - deposit_cycle)%self.min_holding_cycles == 0 and random.random() < self.withdraw_prob:
        withdraw_A_amount, withdraw_B_amount = self.amm.lp_withdraw(share)
        withdraw_tvl = withdraw_A_amount + withdraw_B_amount * self.oracle.get_price()
        deposit_tvl = deposit_A_amount + deposit_B_amount * self.oracle.get_price()

        if withdraw_tvl > deposit_tvl:
          print(deposit_A_amount, deposit_B_amount)
          print(withdraw_A_amount, withdraw_B_amount)
          print("")
        self.result_list.append(((withdraw_tvl / deposit_tvl) - 1) / (cycle - deposit_cycle))
        record_removal_idx.append(i)
    
    record_removal_idx.reverse()
    for i in record_removal_idx:
      self._remove_record_idx(i)
    
    if len(self.deposit_record) >= self.max_deposit_record or random.random() > self.deposit_prob:
      return
    
    deposit_B_amount = self.max_deposit_B_amount * random.random()
    share, deposit_A_amount = self.amm.lp_deposit(deposit_B_amount)

    self.deposit_record.append(tuple([share, deposit_A_amount, deposit_B_amount, cycle]))

  def get_result(self):
    return self.result_list

