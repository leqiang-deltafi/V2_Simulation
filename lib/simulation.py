# import trading_bots
# import deltafi_amm
# import price_data
# import importlib
# importlib.reload(trading_bots)
# importlib.reload(deltafi_amm)
# importlib.reload(price_data)

from .price_data import Oracle
from .prototypes import AMM, LPBot
from .trading_bots import RetailAgent, ArbAgent
import random

def run_lp_simulation(
  num_retail_traders, num_arb_traders, trade_prob, 
  oracle: Oracle, amm_list: list[AMM], 
  plt=None, max_steps=None, title=""):
  
  lp_bots: list[LPBot] = [
    amm.get_lp_bot() for amm in amm_list
  ]

  if max_steps is None:
    max_steps = oracle.max_index
  retail_traders = [RetailAgent(oracle) for _ in range(num_retail_traders)]
  arb_traders = [ArbAgent(oracle) for _ in range(num_arb_traders)]
  traders = retail_traders + arb_traders
  steps = 0
  tvl_ratio_change_list = [[] for _ in range(len(amm_list))]

  for cycle in range(max_steps):
    random.shuffle(traders)
    selected_len = int(random.random() * len(traders))
    for k in range(len(amm_list)):
      ''' do random swaps first '''
      for j in range(selected_len):
        if random.random() < trade_prob:
          traders[j].maybe_execute_trade(amm_list[k])

      tvl_ratio_change_list[k].append(amm_list[k].get_tvl_ratio_to_initial_state())
      ''' do random lp deposit/withdraw'''
      lp_bots[k].update_record(cycle)

    steps += 1

    if oracle.step_foward() is False:
      break

  steps = [i for i in range(steps)]
  print(lp_bots[0].get_result())


def run_swap_simulation(
  num_retail_traders, num_arb_traders, trade_prob, 
  oracle: Oracle, amm_list: list[AMM], 
  plt=None, max_steps=None, title=""):
  
  if max_steps is None:
    max_steps = oracle.max_index
  retail_traders = [RetailAgent(oracle) for _ in range(num_retail_traders)]
  arb_traders = [ArbAgent(oracle) for _ in range(num_arb_traders)]
  traders = retail_traders + arb_traders
  steps = 0
  tvl_ratio_change_list = [[] for _ in range(len(amm_list))]

  max_y_plot = 0
  min_y_plot = 1000000
  for _ in range(max_steps):
    random.shuffle(traders)
    selected_len = int(random.random() * len(traders))
    for k in range(len(amm_list)):
      for j in range(selected_len):
        if random.random() < trade_prob:
          traders[j].maybe_execute_trade(amm_list[k])

      tvl_ratio_change_list[k].append(amm_list[k].get_tvl_ratio_to_initial_state())
    
    steps += 1

    if oracle.step_foward() is False:
      break

  steps = [i for i in range(steps)]

  if not plt is None:
    plt.figure(figsize = (24,12))

    for i in range(len(amm_list)):
      amm_name = amm_list[i].get_name()
      plt.plot(steps, tvl_ratio_change_list[i], label=amm_name)

      max_y_plot = max(max_y_plot, max(tvl_ratio_change_list[i]))
      min_y_plot = min(min_y_plot, min(tvl_ratio_change_list[i]))

    plt.legend()
    plt.title("num_retail_traders=" + str(num_retail_traders) + "\nnum_arb_traders=" + str(num_arb_traders))
    plt.xlabel("step")
    plt.ylabel("pool tvl compare to the initial state " + title)
    plt.ylim(min_y_plot*0.95, max_y_plot*1.05)
    # plt.gca().set_ylim()
    plt.grid()
    plt.show()
