import datetime
from typing import List

import yfinance as yf
import enum
import argparse
import pandas as pd
import os
import sys


class ShareValue(enum.Enum):
    CLOSE = "Close"
    HIGH = "High"
    LOW = "Low"
    OPEN = "Open"


class AggregateMode(enum.Enum):
    MAX = 'MAX'
    AVG = 'AVG'
    MEDIAN = 'MEDIAN'


def load_stock_data(symbol: str, days: int) -> pd.DataFrame:
    """
    Loads the stock data for n days of the given symbol
    :param symbol:
    :param days:
    :return:
    """
    assert days >= 1, "You have to ask for at least one day of stock data!"
    date_format_str = '%Y-%m-%d'
    now = datetime.datetime.now()
    before_n_days = now - datetime.timedelta(days=days)
    now_str = now.strftime(date_format_str)
    before_str = before_n_days.strftime(date_format_str)
    data = yf.download(symbol, before_str, now_str)

    return data


def get_peak(stock_data: pd.DataFrame,
             share_value_price: ShareValue,
             aggregate_mode: AggregateMode) -> float:
    """
    Gets the maximum value of all entries in `stock_data` in the given mode (High, Low etc.)
    :param stock_data:
    :param share_value_price:
    :return:
    """
    value: float
    if aggregate_mode == AggregateMode.MAX:
        value = stock_data[share_value_price.value].max()
    elif aggregate_mode == AggregateMode.AVG:
        value = stock_data[share_value_price.value].mean()
    elif aggregate_mode == AggregateMode.MEDIAN:
        value = stock_data[share_value_price.value].median()

    return float(value)


def calculate_discount(maximum: float, discount: float = 0.1):
    """
    Calculates at (1 - `discount`) * maximum
    :param maximum:
    :param discount:
    :return:
    """
    assert 0. < discount <= 1., "Discount mus be in range ]0, 1]"
    return maximum * (1. - discount)


def get_stop_loss(symbol: str, days: int, share_value_price: ShareValue, discount: float,
                  aggregate_mode: AggregateMode):
    stock_data = load_stock_data(symbol, days)

    peak = get_peak(stock_data, share_value_price=share_value_price, aggregate_mode=aggregate_mode)
    return calculate_discount(peak, discount=discount)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stop Loss Cowboy')
    parser.add_argument('--stock-file',
                        type=str,
                        default="./stocks.csv",
                        required=False,
                        help="Path to the stock file.")

    parser.add_argument('--init',
                        default=False,
                        required=False,
                        action='store_true',
                        help="Creates an empty stocks file template")

    args = parser.parse_args()

    file_path = args.stock_file
    init = args.init

    if init:
        data = pd.DataFrame(
            [
                ['AAPL', 10, 'HIGH', 0.1, 'MAX'],
                ['AAPL', 10, 'HIGH', 0.1, 'AVG'],
                ['AAPL', 10, 'HIGH', 0.1, 'MEDIAN'],
                ['AAPL', 10, 'CLOSE', 0.1, 'MAX'],
                ['AAPL', 10, 'LOW', 0.1, 'AVG'],
                ['AAPL', 10, 'OPEN', 0.1, 'AVG'],
                ['AAPL', 20, 'HIGH', 0.1, 'MAX'],
                ['AAPL', 20, 'CLOSE', 0.1, 'MAX'],
                ['AAPL', 20, 'LOW', 0.1, 'AVG'],
                ['AAPL', 20, 'OPEN', 0.1, 'AVG'],
            ],
            columns=['Symbol',
                     'Time horizon in days',
                     'Share value price (CLOSE, HIGH, LOW, OPEN)',
                     'Discount',
                     'Aggregate Mode (AVG, MAX)'])

        if os.path.isfile(file_path):
            print(f"The file {file_path} exists already. Please delete it or move it somewhere else before init")
            sys.exit(1)

        data.to_csv(file_path, index=False)
        print(f"File written to {file_path}")
        sys.exit(0)

    if not os.path.isfile(file_path):
        print(f"File does not exist: {file_path}. You can create one using --init.")
        sys.exit(1)

    file = pd.read_csv(file_path)

    stops: List[float] = []
    for i, line in file.iterrows():

        try:
            symbol, days, share_value_price_str, discount, mode_str = \
                [line[0], line[1], line[2].upper(), line[3], line[4].upper()]

            share_value_price: ShareValue

            if share_value_price_str == 'CLOSE':
                share_value_price = ShareValue.CLOSE
            elif share_value_price_str == 'HIGH':
                share_value_price = ShareValue.HIGH
            elif share_value_price_str == 'OPEN':
                share_value_price = ShareValue.OPEN
            elif share_value_price_str == 'LOW':
                share_value_price = ShareValue.LOW
            else:
                print(f"Illegal share value price for symbol `{symbol}` (Line: {line + 1}). Skipping.")
                stops.append(-1.)
                continue

            aggregate_mode = AggregateMode
            if mode_str == 'MAX':
                aggregate_mode = aggregate_mode.MAX
            elif mode_str == 'AVG':
                aggregate_mode = aggregate_mode.AVG
            elif mode_str == 'MEDIAN':
                aggregate_mode = aggregate_mode.MEDIAN
            else:
                print(f"Illegal mode for symbol `{symbol}` (Line: {line + 1}). Skipping.")
                stops.append(-1.)
                continue

            stop = get_stop_loss(symbol=symbol,
                                 days=int(days),
                                 share_value_price=share_value_price,
                                 discount=discount,
                                 aggregate_mode=aggregate_mode,
                                 )
            stops.append(stop)
        except Exception as e:
            stops.append(-1.)
            print(f"Problem at line: {i+1}: {str(e)}. Skipping.")

    now_str = datetime.datetime.now().strftime('%Y-%m-%d:%H:%M') + " (Stop loss proposal)"
    file[now_str] = stops
    file.to_csv(file_path, index=False)

    print(f"File successfully written to {file_path}")

    #print(get_top_loss("AAPL", days=20, mode=Mode.HIGH, discount=0.1))
