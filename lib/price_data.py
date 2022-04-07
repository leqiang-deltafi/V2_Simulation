import pandas as pd
import json
from os.path import exists
import ast
import csv
import random

# this simulation is only about ETH-USDC
# the price in this oracle always refers to number of USDC to buy 1 ETH
class Oracle():
  def __init__(self, price_history, conf_intervals) -> None:
    assert(len(conf_intervals) == len(price_history))
    
    self.price_history = price_history
    self.conf_intervals = conf_intervals
    self.max_index = len(price_history) - 1
    self.index = 0
  
  def step_foward(self):
    if self.index >= self.max_index:
        return False
    self.index += 1
    return True

  def get_price(self):
    return self.price_history[self.index]
  
  def get_conf_interval(self):
    return self.conf_intervals[self.index]

def parse_pyth_data():
  pyth_data_file = "../data/ETH_prices.csv"
  conf_interval_history_filename = "../data/pyth_confidence_internval.json"
  twap_history_filename = "../data/pyth_twap.json"
  price_history_filename = "../data/pyth_price.json"

  with open(pyth_data_file, "r") as eth_prices_csv:
    price_history = []
    slots = []
    twap_history = []
    conf_interval_ratio_list = []
    reader = csv.reader(eth_prices_csv, delimiter="\t")

    for i, line in enumerate(reader):
      if i == 0:
        continue
      line = line[0].split(",")
      price = float(line[7])
      slot = int(line[3])
      twap = float(line[9])

      twap_history.append(twap)
      price_history.append(price)
      slots.append(slot)
      
      conf_interval = float(line[8])
      conf_interval_ratio = conf_interval / price
      conf_interval_ratio_list.append(conf_interval_ratio)

    if not exists(conf_interval_history_filename):
      with open(conf_interval_history_filename, "w") as outputFile:
        outputFile.write(str(conf_interval_ratio_list))
    
    if not exists(twap_history_filename):
      with open(twap_history_filename, "w") as outputFile:
        outputFile.write(str(twap_history))
    
    if not exists(price_history_filename):
      with open(price_history_filename, "w") as outputFile:
        outputFile.write(str(price_history))


def get_pyth_confidence_interval_history():
  conf_interval_history_filename = "../data/pyth_confidence_internval.json"
      
  if not exists(conf_interval_history_filename):
    parse_pyth_data()

  with open(conf_interval_history_filename, "r") as inputFile:
    return ast.literal_eval(inputFile.read())
  
def get_pyth_twap_history():
  twap_history_filename = "../data/pyth_twap.json"
      
  if not exists(twap_history_filename):
    parse_pyth_data()

  with open(twap_history_filename, "r") as inputFile:
    return ast.literal_eval(inputFile.read())
  
def get_pyth_price_history():
  price_history_filename = "../data/pyth_price.json"
      
  if not exists(price_history_filename):
    parse_pyth_data()

  with open(price_history_filename, "r") as inputFile:
    return ast.literal_eval(inputFile.read())

def generate_conf_interval(price_history: list[float]) -> list[float]:
  sample_conf_interval_ratio = get_pyth_confidence_interval_history()
  random_conf_interval = []

  for price in price_history:
    selected_index = int(random.random() * len(sample_conf_interval_ratio))
    random_conf_interval.append(price * sample_conf_interval_ratio[selected_index])

  return random_conf_interval

def get_binance_price_data_history(step_len):
  fileName = "../data/price_history_step-" + str(step_len) + ".json"
  if exists(fileName):
    with open(fileName, "r") as inputFile:
      return ast.literal_eval(inputFile.read())

  json_data = json.load(open("../data/ETH_USDC-trades.json"))
  pandas_data = pd.DataFrame(data=json_data, columns=['timestamp', 'id', 'unnamed', 'side', 'price', 'amount', 'total'])
  pandas_data.id = pandas_data.id.astype(int)

  price_history = [pandas_data.loc[0].price]
  current_timestamp = pandas_data.loc[0].timestamp

  for i in range(len(pandas_data)):
    if pandas_data.loc[i].timestamp > current_timestamp + step_len:
      price_history.append(pandas_data.loc[i].price)
      current_timestamp = pandas_data.loc[i].timestamp

  with open("../data/price_history_step-" + str(step_len) + ".json", "w") as outfile:
    outfile.write(str(price_history))

  return price_history

