import MetaTrader5 as mt
import tkinter as tk
from tkinter import ttk
import threading
import time
 
# Initialize MetaTrader
mt.initialize()
 
# Define constants
PROFIT_THRESHOLD = 0.8  # Profit threshold in points
LOSS_THRESHOLD = -0.4  # Loss threshold in points
 
# Initialize tkinter
root = tk.Tk()
root.title("Trade Bot")
root.geometry("800x600")
root.configure(bg="black")
 
# Define styles
style = ttk.Style(root)
style.configure('TButton', foreground='orange', background='black')
style.configure('TLabel', foreground='orange', background='black')
style.configure('TEntry', foreground='orange', background='black')
style.configure('TCombobox', foreground='orange', background='black')
style.configure('TFrame', background='black')
 
# Heading
heading_frame = ttk.Frame(root, style='TFrame')
heading_frame.pack(pady=10)
 
heading_label = ttk.Label(heading_frame, text="TRADE BOT", style='TLabel', font=("Helvetica", 24))
heading_label.pack()
 
# Create a frame with orange-yellow border and black background for the UI sections
ui_frame = ttk.Frame(root, style='TFrame', borderwidth=2, relief="solid")
ui_frame.pack(fill='both', expand=True, padx=10, pady=10)
 
# Information Display Section
info_frame = ttk.Frame(ui_frame, style='TFrame', borderwidth=1, relief="solid")
info_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
 
info_heading = ttk.Label(info_frame, text="INFO", style='TLabel', font=("Helvetica", 18))
info_heading.pack(pady=5)
 
output_memo = tk.Text(info_frame, height=30, width=50, bg="black", fg="orange")
output_memo.pack(padx=10, pady=10)
 
# Bot Controls Section
controls_frame = ttk.Frame(ui_frame, style='TFrame', borderwidth=1, relief="solid")
controls_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
 
bot_heading = ttk.Label(controls_frame, text="BOT CONTROLS", style='TLabel', font=("Helvetica", 18))
bot_heading.pack(pady=5)
 
# Market Selection Section
market_section = ttk.Frame(controls_frame, style='TFrame')
market_section.pack(pady=5)
 
market_label = ttk.Label(market_section, text="Select Market:", style='TLabel')
market_label.pack(side='left')
 
market_combobox = ttk.Combobox(market_section, values=["BTCUSD", "ETHUSD", "EURUSD", "GOLD", "NMRUSD"], style='TCombobox')
market_combobox.pack(side='left')
market_combobox.set("BTCUSD")  # Pre-select a default value
 
# Login Section
login_section = ttk.Frame(controls_frame, style='TFrame')
login_section.pack(pady=5)
 
login_label = ttk.Label(login_section, text="Enter Login:", style='TLabel')
login_label.pack(side='left')
 
login_entry = ttk.Entry(login_section, style='TEntry')
login_entry.pack(side='left')
login_entry.insert(0, "97011152")  # Pre-fill with login value
 
# Password Section
password_section = ttk.Frame(controls_frame, style='TFrame')
password_section.pack(pady=5)
 
password_label = ttk.Label(password_section, text="Enter Password:", style='TLabel')
password_label.pack(side='left')
 
password_entry = ttk.Entry(password_section, style='TEntry', show='*')
password_entry.pack(side='left')
password_entry.insert(0, "Josh2022569.")  # Pre-fill with password value
 
# Server Section
server_section = ttk.Frame(controls_frame, style='TFrame')
server_section.pack(pady=5)
 
server_label = ttk.Label(server_section, text="Enter Server:", style='TLabel')
server_label.pack(side='left')
 
server_entry = ttk.Entry(server_section, style='TEntry')
server_entry.pack(side='left')
server_entry.insert(0, "XMGlobal-MT5 5")  # Pre-fill with server value
 
# Quantity Section
qty_section = ttk.Frame(controls_frame, style='TFrame')
qty_section.pack(pady=5)
 
qty_label = ttk.Label(qty_section, text="Enter Quantity:", style='TLabel')
qty_label.pack(side='left')
 
qty_entry = ttk.Entry(qty_section, style='TEntry')
qty_entry.pack(side='left')
 
# Start and End Bot Buttons Section
bot_buttons_section = ttk.Frame(controls_frame, style='TFrame')
bot_buttons_section.pack(pady=10)
 
start_button = ttk.Button(bot_buttons_section, text="Start Bot", style='TButton')
start_button.pack(side='left', padx=5)
 
end_button = ttk.Button(bot_buttons_section, text="End Bot", style='TButton')
end_button.pack(side='left', padx=5)
 
# Create a dictionary to keep track of running threads for each market
running_threads = {}
 
# Define trading functions
def create_order(ticker, qty, order_type, price):
    try:
        request = {
            "action": mt.TRADE_ACTION_DEAL,
            "symbol": ticker,
            "volume": qty,
            "type": order_type,
            'price': price,
            'comment': 'Python Open Position',
            'type_time': mt.ORDER_TIME_GTC,
            'type_filling': mt.ORDER_FILLING_IOC
        }
        result = mt.order_send(request)
        if result.retcode == mt.TRADE_RETCODE_DONE:
            update_output_memo(f"Order created: {result}")
        else:
            update_output_memo(f"Failed to create order: {result.comment}")
    except Exception as e:
        update_output_memo(f"Error placing order: {e}")
 
def close_order(ticket):
    try:
        request = {
            "action": mt.TRADE_ACTION_DEAL,
            "position": ticket,
        }
        result = mt.order_send(request)
        if result.retcode == mt.TRADE_RETCODE_DONE:
            update_output_memo(f"Order closed: {result}")
        else:
            update_output_memo(f"Failed to close order: {result.comment}")
    except Exception as e:
        update_output_memo(f"Error closing order: {e}")
 
def is_market_open(ticker):
    symbol_info = mt.symbol_info(ticker)
    if symbol_info is not None:
        return symbol_info.trade_mode == mt.SYMBOL_TRADE_MODE_FULL
    return False
 
def run_bot(market, login, password, server, qty):
    last_pattern = None
    open_prices = {}  # Dictionary to store the opening prices of trades
    running = True  # Flag to control loop
    while running:
        try:
            if is_market_open(market):
                # Fetch OHLC data for the last five candles
                rates = mt.copy_rates_from_pos(market, mt.TIMEFRAME_M1, 0, 5)
                if rates is not None and len(rates) >= 5:
                    current_close = rates[-1][4]
                    prev_high = max(r[2] for r in rates[:-1])
                    prev_low = min(r[3] for r in rates[:-1])
                   
                    # Predict next high and low
                    next_high = current_close + (current_close - prev_low)
                    next_low = current_close - (prev_high - current_close)
                   
                    # Check if pattern changed
                    current_pattern = 'Up' if current_close > prev_high else 'Down' if current_close < prev_low else 'Flat'
                    update_output_memo(f"Current Pattern: {current_pattern}")
                   
                    if current_pattern != last_pattern:
                        # Close existing orders
                        positions = mt.positions_get(symbol=market)
                        if positions:
                            for position in positions:
                                if position.ticket > 0:  # Ensure ticket number is valid
                                    close_order(position.ticket)
                        last_pattern = current_pattern
                        # Create new orders
                        buy_price = mt.symbol_info_tick(market).ask
                        sell_price = mt.symbol_info_tick(market).bid
                        update_output_memo(f"Buy Price: {buy_price}, Sell Price: {sell_price}")
                        if current_pattern == 'Up':
                            create_order(market, qty, mt.ORDER_TYPE_BUY, buy_price)
                            open_prices[market] = buy_price  # Record opening price
                        elif current_pattern == 'Down':
                            create_order(market, qty, mt.ORDER_TYPE_SELL, sell_price)
                            open_prices[market] = sell_price  # Record opening price
                    else:
                        # Check profit/loss and close trades if thresholds are met
                        for position in mt.positions_get(symbol=market):
                            if position.ticket in open_prices:
                                open_price = open_prices[position.ticket]
                                current_price = mt.symbol_info_tick(market).bid if position.type == mt.ORDER_TYPE_SELL else mt.symbol_info_tick(market).ask
                                profit_loss = current_price - open_price if position.type == mt.ORDER_TYPE_BUY else open_price - current_price
                                if profit_loss >= PROFIT_THRESHOLD:
                                    close_order(position.ticket)
                                    update_output_memo(f"Trade closed due to reaching profit threshold: Ticket {position.ticket}")
                                elif profit_loss <= LOSS_THRESHOLD:
                                    close_order(position.ticket)
                                    update_output_memo(f"Trade closed due to reaching loss threshold: Ticket {position.ticket}")
                   
                    time.sleep(120)  # Wait for 2 minutes
                else:
                    update_output_memo("Insufficient data")
                    time.sleep(10)
            else:
                update_output_memo("Market is closed. Waiting for it to open...")
                time.sleep(300)  # Wait for 5 minutes if the market is closed
        except Exception as e:
            update_output_memo(f"An error occurred: {str(e)}")
            time.sleep(10)
 
# Bind start button to start_bot function
def start_bot():
    market = market_combobox.get()
    login = login_entry.get()
    password = password_entry.get()
    server = server_entry.get()
    qty = float(qty_entry.get())
    if market and login and password and server:
        mt.login(login, password, server)
        update_output_memo(f"Bot started for {market} with login {login}")
        start_button.config(state="disabled")
        # Check if the bot is already running for the selected market
        if market not in running_threads:
            # Start a new thread for the market
            trading_thread = threading.Thread(target=run_bot, args=(market, login, password, server, qty))
            trading_thread.start()
            running_threads[market] = {'thread': trading_thread, 'running': True}
        else:
            update_output_memo(f"Bot is already running for {market}")
 
# Bind end button to end_bot function
def end_bot():
    market = market_combobox.get()
    if market in running_threads:
        # Set flag to signal thread to stop
        running_threads[market]['running'] = False
        del running_threads[market]
        update_output_memo(f"Bot stopped for {market}")
    else:
        update_output_memo(f"Bot is not running for {market}")
    start_button.config(state="normal")
 
start_button.config(command=start_bot)
end_button.config(command=end_bot)
 
def update_output_memo(message):
    def update_message():
        output_memo.insert(tk.END, message + '\n')
    output_memo.after(0, update_message)
 
root.mainloop()