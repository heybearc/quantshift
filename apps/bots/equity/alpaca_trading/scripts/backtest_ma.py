import backtrader as bt
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MAStrategy(bt.Strategy):
    """
    Moving Average Crossover Strategy
    - Buy when short-term MA crosses above long-term MA
    - Sell when short-term MA crosses below long-term MA
    """
    params = (
        ('short_window', 5),
        ('long_window', 20),
        ('printlog', True)
    )

    def log(self, txt, dt=None, doprint=False):
        """ Logging function for this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # Add Moving Averages
        self.ma_short = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.short_window)
        self.ma_long = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.long_window)
        
        # Indicators for the plotting
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25).subplot = True
        bt.indicators.Stochastic(self.datas[0])

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset orders
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        
        # Check if an order is pending
        if self.order:
            return
            
        # Check if we are in the market
        if not self.position:
            # Not yet in the market, check for buy signal
            if self.ma_short[0] > self.ma_long[0] and self.ma_short[-1] <= self.ma_long[-1]:
                self.log(f'BUY CREATE, {self.dataclose[0]:.2f}')
                self.order = self.buy()
        else:
            # Already in the market, check for sell signal
            if self.ma_short[0] < self.ma_long[0] and self.ma_short[-1] >= self.ma_long[-1]:
                self.log(f'SELL CREATE, {self.dataclose[0]:.2f}')
                self.order = self.sell()

def run_backtest(symbol='AAPL', start_date='2020-01-01', end_date=None, 
                initial_cash=10000.0, commission=0.001, stake=1):
    """
    Run backtest for the MA Crossover Strategy
    
    Args:
        symbol (str): Stock symbol to backtest
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format (default: today)
        initial_cash (float): Initial cash for the backtest
        commission (float): Broker commission
        stake (int): Number of shares to trade
    """
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Add a strategy
    cerebro.addstrategy(MAStrategy)
    
    # Load data from Yahoo Finance
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    data = bt.feeds.YahooFinanceData(
        dataname=symbol,
        fromdate=datetime.strptime(start_date, '%Y-%m-%d'),
        todate=datetime.strptime(end_date, '%Y-%m-%d'),
        reverse=False
    )
    
    # Add the data to Cerebro
    cerebro.adddata(data)
    
    # Set our desired cash start
    cerebro.broker.setcash(initial_cash)
    
    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=stake)
    
    # Set the commission
    cerebro.broker.setcommission(commission=commission)
    
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Run over everything
    results = cerebro.run()
    
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Plot the result
    cerebro.plot(style='candlestick')

if __name__ == '__main__':
    # Example usage
    run_backtest(
        symbol='AAPL',
        start_date='2020-01-01',
        end_date='2023-01-01',
        initial_cash=10000.0,
        commission=0.001,
        stake=1
    )
