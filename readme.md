# Stop Loss Cowboy
Calculates a stop loss proposal based on a simple heuristic

## Get started
Prerequisites:
- Python 3.X

Install the requirements of the project:
- Download those files and `cd` into the directory.
- `pip install -r requirements.txt`

Create an example file and edit it to your desires. You should use
some csv-formatting program for that: <br />
`python main.py --init`

run the program: <br />
`python main.py`

you can optionally specify another file path by specifying the attribute
`--stock-file`.

You do not need to create a fresh file each time. New results will create a new column
each time you run the program.

## File entry format
an entry within the stocks file looks like that:
`AAPL,10,HIGH,0.1,MAX`:
- `AAPL` is the stock of interest
- `10` are the amount of days before today taken into account
- `HIGH` is the stock price value taken into account (here the highest price of each day). Can also be `LOW` or `CLOSE` or `OPEN`
- `0.1` is the value the aggregated value is reduced (here the highest value of the last 10 days it reduced by `10%`)
- `MAX` is the aggregation function over those `10` days. Can also be `MEAN` or `MEDIAN`.