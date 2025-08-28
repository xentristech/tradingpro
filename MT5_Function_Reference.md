# REFERENCIA DE FUNCIONES MT5 - Scrapeado de MQL5.com
============================================================
Generado: 2025-08-28 12:27:40
Total funciones: 32

## Sin categoría
----------------------------------------

### mt5initialize_py
**Descripción:** Sin descripción


### mt5login_py
**Descripción:** Sin descripción


### mt5shutdown_py
**Descripción:** Sin descripción


### mt5version_py
**Descripción:** Sin descripción
**Parámetros:**
- `integer`: MetaTrader 5 terminal version
- `integer`: Build
- `string`: Build release date


### mt5lasterror_py
**Descripción:** Sin descripción
**Parámetros:**
- `RES_S_OK`: 1
- `RES_E_FAIL`: -1
- `RES_E_INVALID_PARAMS`: -2
- `RES_E_NO_MEMORY`: -3
- `RES_E_NOT_FOUND`: -4
- `RES_E_INVALID_VERSION`: -5
- `RES_E_AUTH_FAILED`: -6
- `RES_E_UNSUPPORTED`: -7
- `RES_E_AUTO_TRADING_DISABLED`: -8
- `RES_E_INTERNAL_FAIL`: -10000
- `RES_E_INTERNAL_FAIL_SEND`: -10001
- `RES_E_INTERNAL_FAIL_RECEIVE`: -10002
- `RES_E_INTERNAL_FAIL_INIT`: -10003
- `RES_E_INTERNAL_FAIL_CONNECT`: -10003
- `RES_E_INTERNAL_FAIL_TIMEOUT`: -10005


### mt5accountinfo_py
**Descripción:** Sin descripción


### mt5terminalinfo_py
**Descripción:** Sin descripción


### mt5symbolstotal_py
**Descripción:** Sin descripción


### mt5symbolsget_py
**Descripción:** Sin descripción


### mt5symbolinfo_py
**Descripción:** Sin descripción


### mt5symbolinfotick_py
**Descripción:** Sin descripción


### mt5symbolselect_py
**Descripción:** Sin descripción


### mt5marketbookadd_py
**Descripción:** Sin descripción


### mt5marketbookget_py
**Descripción:** Sin descripción


### mt5marketbookrelease_py
**Descripción:** Sin descripción


### mt5copyratesfrom_py
**Descripción:** Sin descripción
**Parámetros:**
- `TIMEFRAME_M1`: 1 minute
- `TIMEFRAME_M2`: 2 minutes
- `TIMEFRAME_M3`: 3 minutes
- `TIMEFRAME_M4`: 4 minutes
- `TIMEFRAME_M5`: 5 minutes
- `TIMEFRAME_M6`: 6 minutes
- `TIMEFRAME_M10`: 10 minutes
- `TIMEFRAME_M12`: 12 minutes
- `TIMEFRAME_M12`: 15 minutes
- `TIMEFRAME_M20`: 20 minutes
- `TIMEFRAME_M30`: 30 minutes
- `TIMEFRAME_H1`: 1 hour
- `TIMEFRAME_H2`: 2 hours
- `TIMEFRAME_H3`: 3 hours
- `TIMEFRAME_H4`: 4 hours
- `TIMEFRAME_H6`: 6 hours
- `TIMEFRAME_H8`: 8 hours
- `TIMEFRAME_H12`: 12 hours
- `TIMEFRAME_D1`: 1 day
- `TIMEFRAME_W1`: 1 week
- `TIMEFRAME_MN1`: 1 month


### mt5copyratesfrompos_py
**Descripción:** Sin descripción


### mt5copyratesrange_py
**Descripción:** Sin descripción


### mt5copyticksfrom_py
**Descripción:** Sin descripción
**Parámetros:**
- `COPY_TICKS_ALL`: all ticks
- `COPY_TICKS_INFO`: ticks containing Bid and/or Ask price changes
- `COPY_TICKS_TRADE`: ticks containing Last and/or Volume price changes
- `TICK_FLAG_BID`: Bid price changed
- `TICK_FLAG_ASK`: Ask price changed
- `TICK_FLAG_LAST`: Last price changed
- `TICK_FLAG_VOLUME`: Volume changed
- `TICK_FLAG_BUY`: last Buy price changed
- `TICK_FLAG_SELL`: last Sell price changed


### mt5copyticksrange_py
**Descripción:** Sin descripción


### mt5orderstotal_py
**Descripción:** Sin descripción


### mt5ordersget_py
**Descripción:** Sin descripción


### mt5ordercalcmargin_py
**Descripción:** Sin descripción
**Parámetros:**
- `ORDER_TYPE_BUY`: Market buy order
- `ORDER_TYPE_SELL`: Market sell order
- `ORDER_TYPE_BUY_LIMIT`: Buy Limit pending order
- `ORDER_TYPE_SELL_LIMIT`: Sell Limit pending order
- `ORDER_TYPE_BUY_STOP`: Buy Stop pending order
- `ORDER_TYPE_SELL_STOP`: Sell Stop pending order
- `ORDER_TYPE_BUY_STOP_LIMIT`: Upon reaching the order price, Buy Limit pending order is placed at StopLimit price
- `ORDER_TYPE_SELL_STOP_LIMIT`: Upon reaching the order price, Sell Limit pending order is placed at StopLimit price
- `ORDER_TYPE_CLOSE_BY`: Order for closing a position by an opposite one


### mt5ordercalcprofit_py
**Descripción:** Sin descripción


### mt5ordercheck_py
**Descripción:** Sin descripción
**Parámetros:**
- `TRADE_ACTION_DEAL`: Place an order for an instant deal with the specified parameters (set a market order)
- `TRADE_ACTION_PENDING`: Place an order for performing a deal at specified conditions (pending order)
- `TRADE_ACTION_SLTP`: Change open position Stop Loss and Take Profit
- `TRADE_ACTION_MODIFY`: Change parameters of the previously placed trading order
- `TRADE_ACTION_REMOVE`: Remove previously placed pending order
- `TRADE_ACTION_CLOSE_BY`: Close a position by an opposite one
- `ORDER_FILLING_FOK`: This execution policy means that an order can be executed only in the specified volume. If the necessary amount of a financial instrument is currently unavailable in the market, the order will not be executed. The desired volume can be made up of several available offers.
- `ORDER_FILLING_IOC`: An agreement to execute a deal at the maximum volume available in the market within the volume specified in the order. If the request cannot be filled completely, an order with the available volume will be executed, and the remaining volume will be canceled.
- `ORDER_FILLING_RETURN`: This policy is used only for market (ORDER_TYPE_BUY and ORDER_TYPE_SELL), limit and stop limit orders (ORDER_TYPE_BUY_LIMIT, ORDER_TYPE_SELL_LIMIT, ORDER_TYPE_BUY_STOP_LIMIT and ORDER_TYPE_SELL_STOP_LIMIT) and only for the symbols with Market or Exchange execution modes. If filled partially, a market or limit order with the remaining volume is not canceled, and is processed further.
During activation of the ORDER_TYPE_BUY_STOP_LIMIT and ORDER_TYPE_SELL_STOP_LIMIT orders, an appropriate limit order ORDER_TYPE_BUY_LIMIT/ORDER_TYPE_SELL_LIMIT with the ORDER_FILLING_RETURN type is created.
- `ORDER_TIME_GTC`: The order stays in the queue until it is manually canceled
- `ORDER_TIME_DAY`: The order is active only during the current trading day
- `ORDER_TIME_SPECIFIED`: The order is active until the specified date
- `ORDER_TIME_SPECIFIED_DAY`: The order is active until 23:59:59 of the specified day. If this time appears to be out of a trading session, the expiration is processed at the nearest trading time.


### mt5ordersend_py
**Descripción:** Sin descripción
**Parámetros:**
- `action`: Trading operation type. The value can be one of the values of the TRADE_REQUEST_ACTIONS enumeration
- `magic`: EA ID. Allows arranging the analytical handling of trading orders. Each EA can set a unique ID when sending a trading request
- `order`: Order ticket. Required for modifying pending orders
- `symbol`: The name of the trading instrument, for which the order is placed. Not required when modifying orders and closing positions
- `volume`: Requested volume of a deal in lots. A real volume when making a deal depends on an order execution type.
- `price`: Price at which an order should be executed. The price is not set in case of market orders for instruments of the "Market Execution" (SYMBOL_TRADE_EXECUTION_MARKET) type having the TRADE_ACTION_DEAL type
- `stoplimit`: A price a pending Limit order is set at when the price reaches the 'price' value (this condition is mandatory). The pending order is not passed to the trading system until that moment
- `sl`: A price a Stop Loss order is activated at when the price moves in an unfavorable direction
- `tp`: A price a Take Profit order is activated at when the price moves in a favorable direction
- `deviation`: Maximum acceptable deviation from the requested price, specified in points
- `type`: Order type. The value can be one of the values of the ORDER_TYPE enumeration
- `type_filling`: Order filling type. The value can be one of the ORDER_TYPE_FILLING values
- `type_time`: Order type by expiration. The value can be one of the ORDER_TYPE_TIME values
- `expiration`: Pending order expiration time (for TIME_SPECIFIED type orders)
- `comment`: Comment to an order
- `position`: Position ticket. Fill it when changing and closing a position for its clear identification. Usually, it is the same as the ticket of the order that opened the position.
- `position_by`: Opposite position ticket. It is used when closing a position by an opposite one (opened at the same symbol but in the opposite direction).


### mt5positionstotal_py
**Descripción:** Sin descripción


### mt5positionsget_py
**Descripción:** Sin descripción


### mt5historyorderstotal_py
**Descripción:** Sin descripción


### mt5historyordersget_py
**Descripción:** Sin descripción


### mt5historydealstotal_py
**Descripción:** Sin descripción


### mt5historydealsget_py
**Descripción:** Sin descripción
