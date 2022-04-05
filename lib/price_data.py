import pandas as pd
import json
from os.path import exists
import ast


# this simulation is only about ETH-USDC
# the price in this oracle always refers to number of USDC to buy 1 ETH
class Oracle():
    def __init__(self, price_history, conf_intervals=None) -> None:
        if conf_intervals is None:
            conf_intervals = [0] * len(price_history)
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



get_binance_price_data_history(1000)

