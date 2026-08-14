# Evidence: 2026-07-27 Recorder Sample Audit

Status: Point-in-time evidence  
Audit date: 2026-08-10  
Scope: One local daily archive only

## Artifact

Audited file:
`drive-download-20260810T091218Z-1-001.zip`

Archive members:

| Member | Compressed member size |
| --- | ---: |
| `recorder.log.2026-07-27.gz` | 148,617 bytes |
| `binance_raw_events_2026-07-27.jsonl.gz` | 153,970,117 bytes |
| `polymarket_raw_events_2026-07-27.jsonl.gz` | 294,987,232 bytes |

The audit streamed the compressed JSONL members without extracting them. JSON
records were counted and inspected by event type and timestamp.

## Observed: Binance

- 10,092,865 records; zero malformed JSON records.
- Receipt coverage: `2026-07-27T00:00:00.045186Z` through
  `2026-07-27T23:59:59.974235Z`.
- Event counts:
  - 9,257,161 `btcusdt@bookTicker`
  - 750,295 `btcusdt@aggTrade`
  - 85,409 `btcusdt@kline_1s`
- There were 85,409 unique closed one-second kline starts versus 86,400 seconds
  in the UTC day.
- Each of the three streams had six receipt gaps longer than 30 seconds.
- The maximum observed gap was approximately 487 seconds.
- No backward receipt timestamps were found within a stream.

## Observed: Polymarket

- 3,423,549 wrapper records; zero malformed JSON records.
- Receipt coverage: `2026-07-27T00:00:00.061155Z` through
  `2026-07-27T23:59:59.999587Z`.
- 289 distinct five-minute slugs were present.
- Channel counts:
  - 3,259,683 `price_change`
  - 110,664 `book`
  - 52,625 `last_trade_price`
  - 288 `market_metadata`
  - 289 `unknown_payload`
- The `unknown_payload` records inspected were initial array-form order-book
  snapshots. Their contents are recoverable even though the recorder did not
  classify the wrapper correctly.
- For events aligned by the Unix timestamp suffix in their market slug:
  - 773,088 arrived from 300 seconds before start up to the start;
  - 2,650,461 arrived from market start onward;
  - the earliest relative receipt was about -299.77 seconds;
  - the latest relative receipt in the entire file was about +29.77 seconds.
- Consequently, no recorded Polymarket event was associated with seconds 30
  through 300 of its five-minute active window.
- For raw events carrying an exchange timestamp, mean receipt latency was about
  0.175 seconds; observed values ranged from about 0.077 to 7.253 seconds.
- No backward wrapper receipt timestamps were found within a channel.

## Observed: Metadata and Recorder Diagnostics

- Market metadata preserves explicit UP and DOWN token IDs.
- A metadata example for slug `btc-updown-5m-1785110700` labels
  `2026-07-26T00:12:41.574435Z` as `window_start_utc`, although the slug and
  question identify a five-minute interval starting at `2026-07-27T00:05:00Z`.
  That field must not be treated as the prediction-window start without further
  validation.
- Recorder heartbeats repeatedly reported zero parsed top-book, trade, and price
  change events while the raw archive contained those event types. Those derived
  counters are not reliable evidence of raw-event absence.
- No Chainlink BTC/USD stream or explicit `market_resolved` channel was found in
  the archive.

## Established External Facts

- These BTC five-minute markets resolve using Chainlink BTC/USD rather than a
  Binance spot pair. Polymarket market rules:
  <https://polymarket.com/event/btc-updown-5m-1778982000?outcomeIndex=0>
- Polymarket's RTDS supports real-time Chainlink `btc/usd` data:
  <https://docs.polymarket.com/market-data/websocket/rtds>
- Polymarket's market WebSocket can emit `market_resolved` with a winning asset
  and outcome when the custom feature is enabled:
  <https://docs.polymarket.com/market-data/websocket/market-channel>
- Binance documents one-second kline updates and UTC event timestamps:
  <https://developers.binance.com/zh-CN/docs/products/spot/testnet/web-socket-streams>

## Inferences Requiring Broader Verification

- The discovery/subscription logic appears to follow the upcoming market during
  most of its pre-open period and retain it for only the beginning of its active
  period.
- Binance-derived `price_to_beat` values in the recorder log should not be
  assumed identical to the Chainlink settlement reference.
- The raw sample may support BTC feature research and very-early-window market
  analysis after cleaning, but it cannot support full-window execution
  backtesting by itself.

## Limitations

- Only one of the reported 30 days was audited.
- The audit did not verify economic correctness of every order-book transition.
- Historical label or Chainlink-data recovery was not attempted.
- Findings must not be generalized to all daily archives until the same checks
  are run across their manifest.

