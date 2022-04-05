from secrets import randbits
from prototypes import TradingBot, AMM
from price_data import Oracle
import random

# class that simulates regular traders (robinhood traders)
class RetailAgent(TradingBot):
    def __init__(self, oracle: Oracle) -> None:
        self.oracle = oracle
        self.max_sell_A_amount = 2000 * random()
        self.max_sell_B_amount = self.max_sell_A_amount / oracle.get_price()
        self.accepted_price_range = 0.1 * random()

    def maybe_sell_A_for_B(self, amm: AMM):
        price_A_selling_A = 1 / self.oracle.get_price()
        sell_A_amount = self.max_sell_A_amount * random.random()
        accepted_min_B_amount = sell_A_amount * price_A_selling_A * (1 - self.accepted_price_range * random.random())
        amm_buy_B_amount = amm.get_swap_out_B(sell_A_amount)

        if amm_buy_B_amount > accepted_min_B_amount:
            amm.swap_A_for_B(sell_A_amount)
    
    def maybe_sell_B_for_A(self, amm: AMM):
        price_B_selling_B = self.oracle.get_price()
        sell_B_amount = self.max_sell_B_amount * random.random()
        accept_min_A_amount = sell_B_amount * price_B_selling_B * (1 - self.accepted_price_range * random.random())
        amm_buy_A_amount = amm.get_swap_out_A(sell_B_amount)

        if amm_buy_A_amount > accept_min_A_amount:
            amm.swap_B_for_A(sell_B_amount)
    
    def maybe_execute_trade(self, amm: AMM):
        if random.random() < 0.5:
            self.maybe_sell_A_for_B(amm)
        else:
            self.maybe_sell_B_for_A(amm)


# Trading bot class that simulates the behavior of arbitraguer
# An arbitraguer buy at our amm with low price and sell at other exchange with high price
# to get net gain on one token (we only simulate the behavior the arbitraguers swap at our amm)
class ArbAgent(TradingBot):
    def __init__(self, oracle: Oracle) -> None:
        self.oracle = oracle

    # buy B for less A at our AMM, then sell B for more A in other places
    # the arbitraguer gets net gain on A
    def arbitrage_A(self, implied_price_A_sell_A, target_price_B_sell_B, amm: AMM):
        sell_A_amount = amm.get_balance_A() * 0.1
        buy_B_amount = amm.get_swap_out_B(sell_A_amount)

        while sell_A_amount > 0.000001 and (buy_B_amount / sell_A_amount) * target_price_B_sell_B <= 1:
            sell_A_amount /= 2
            buy_B_amount = amm.get_balance_B(sell_A_amount)

        if (buy_B_amount / sell_A_amount) * target_price_B_sell_B > 1:
            amm.swap_A_for_B(sell_A_amount)
    
    # buy A for less B at our AMM, then sell A for more B in other places
    # the arbitraguer gets net gain on B
    def arbitrage_B(self, implied_price_B_sell_B, target_price_A_sell_A, amm: AMM):
        sell_B_amount = amm.get_balance_B() * 0.1
        buy_A_amount = amm.get_swap_out_A(sell_B_amount)

        while sell_B_amount > 0.000000001 and (buy_A_amount / sell_B_amount) * target_price_A_sell_A <= 1:
            sell_B_amount /= 2
            buy_A_amount = amm.get_balance_A(sell_B_amount)

        if (buy_A_amount / sell_B_amount) * target_price_A_sell_A > 1:
            amm.swap_B_for_A(sell_B_amount)

    def maybe_execute_trade(self, amm: AMM):
        target_price_A_sell_A = 1 / (self.oracle.get_price() + (2*random.random() - 1)*self.oracle.get_conf_interval())
        target_price_B_sell_B = self.oracle.get_price() + (2*random.random() - 1)*self.oracle.get_conf_interval()

        implied_price_B_sell_B = amm.get_implied_price_B_for_A()
        implied_price_A_sell_A = amm.get_implied_price_A_for_B()

        if implied_price_A_sell_A * target_price_B_sell_B > 1:
            self.arbitrage_A(implied_price_A_sell_A, target_price_B_sell_B, amm)
        
        if implied_price_B_sell_B * target_price_A_sell_A > 1:
            self.arbitrage_B(implied_price_B_sell_B, target_price_A_sell_A, amm)

