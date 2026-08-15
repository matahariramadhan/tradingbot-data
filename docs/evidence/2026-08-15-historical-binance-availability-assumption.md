# Historical Binance Availability Assumption

Date: 2026-08-15 UTC

## Scope

This evidence supports the beginner historical Binance 15-minute direction
dataset. It does not change the receipt-time policy of the recorder-backed
five-minute proxy pipeline.

## Observed interface distinction

Binance Spot REST `GET /api/v3/klines` returns a 12-field kline record with
open time, OHLCV values, close time, quote volume, trade count, and taker-buy
volumes. The documented response does not include when a particular client
received the record. Binance's WebSocket kline payload includes Binance event
time, interval start/close times, and a closed flag, but event time is still
not the local recorder receipt time.

Sources:

- [Binance Spot REST market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market#klinecandlestick-data)
- [Binance Spot WebSocket kline-stream documentation](https://developers.binance.com/zh-CN/docs/products/spot/testnet/web-socket-streams)

## Accepted project consequence

For the active beginner slice, use historical 1-minute klines and declare the
availability policy `interval_complete_assumption`: a completed interval is
treated as available after its interval closes. Do not claim original
receipt-time verification. Later compare this simplified dataset against
recorder data carrying `received_at_utc`.
