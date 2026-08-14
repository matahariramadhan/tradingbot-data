# Machine Learning Learning Project

## Building a 24/7 Short-Term BTC → Polymarket Trading Research System

## 1. Project Purpose

The primary goal is to **learn machine learning by building a real end-to-end project**.

The project uses short-term BTC prediction markets on Polymarket as the practical domain.

The eventual system should be able to:

- collect BTC, settlement/reference, and Polymarket data;
- analyze current market conditions;
- estimate the probability of Up or Down resolution;
- recognize situations where the model historically performs poorly;
- compare predicted probability with executable Polymarket prices;
- decide between Trade and No Trade;
- backtest the strategy realistically;
- operate continuously in paper/shadow mode;
- and eventually support automated execution if sufficient evidence of an edge exists.

The project is first an **ML and research project**, not a race to deploy a profitable trading bot.

---

# 2. Core Research Hypothesis

The project begins from a personal trading observation:

> Short-term BTC outcomes may be easier to predict when the underlying BTC market is in a strong directional regime and significantly harder when price is near equilibrium, choppy, or repeatedly crossing the strike/reference level.

This observation is a hypothesis, not an established fact.

The project should test questions such as:

- Does model performance improve during strong directional regimes?
- Which measurable characteristics make a market more predictable?
- When does prediction accuracy collapse toward randomness?
- Does distance from the strike matter relative to current volatility?
- Does the probability of reversal increase under particular conditions?
- Can the system reliably recognize situations where it should not trade?

A major principle of the project is:

> **No Trade is a legitimate model decision.**

---

# 3. Instructor and Learning Quality Requirements

The quality of the project must not depend entirely on the instructor's existing competency.

The instructor should act as:

- teacher;
- research mentor;
- code reviewer;
- technical reviewer;
- critical challenger.

Technical claims should preferably be supported by:

1. official documentation;
2. research papers;
3. reputable textbooks;
4. established statistical or machine-learning references.

The instructor should explicitly distinguish between:

```text
Established knowledge
Project-specific design choice
Personal opinion
Experimental hypothesis
Unknown / needs verification
```

If the instructor does not know something confidently, the expected response is:

> "We need to verify this."

Researching an answer is preferable to teaching an incorrect assumption confidently.

Working code alone is not considered evidence of learning.

For every major component, the student should eventually be able to explain:

- what problem it solves;
- why the method is appropriate;
- what assumptions it makes;
- how it could fail;
- how it is evaluated;
- what alternatives exist.

Complexity should also be earned.

Do not begin with Transformers, LSTMs, reinforcement learning, or other advanced models unless simpler approaches have demonstrated a meaningful limitation.

---

# Phase 1 — Problem Definition, Market Mechanics, and Data Foundations

## Objective

Understand precisely what is being predicted and build the foundations required to work with financial time-series data.

Before training any model, define:

- prediction target;
- market duration;
- settlement/reference mechanism;
- what information exists at prediction time;
- when predictions are generated;
- when a position may be entered;
- what constitutes Up and Down;
- what constitutes Trade and No Trade;
- and how success will eventually be measured.

A critical distinction must be maintained between:

```text
BTC market data
        ↓
Predictive information

Settlement/reference data
        ↓
Determines final outcome

Polymarket market data
        ↓
Determines trading price
```

These are related but not identical.

## Learning Topics

Learn the Python and data concepts necessary for the project:

- NumPy;
- Pandas or Polars;
- time-series data;
- timestamps;
- time zones;
- joins;
- missing data;
- resampling;
- rolling windows;
- data visualization;
- API fundamentals;
- WebSocket fundamentals.

Basic probability should also begin here:

- probability;
- conditional probability;
- expected value;
- variance;
- binary outcomes.

## Practical Work

Use historical BTC data to calculate basic features such as:

```text
returns
rolling returns
price range
rolling volatility
volume
momentum
distance from a reference level
rolling highs/lows
```

The student should become comfortable manipulating market data before introducing ML.

## Deliverable

A documented dataset pipeline or notebook that:

1. loads raw BTC market data;
2. cleans and synchronizes it;
3. produces basic time-series features;
4. visualizes several market conditions;
5. clearly defines the eventual ML prediction problem.

---

# Phase 2 — Build the Research Dataset and Investigate the Trading Hypotheses

## Objective

Build the dataset required for the actual project and start testing the original trading observations scientifically.

The dataset should eventually combine several synchronized sources.

## BTC Market Data

Potential information:

```text
price
returns
volume
trades
bid/ask
spread
order-book depth
volatility
trade imbalance
```

## Polymarket Data

Potential information:

```text
market ID
market start
market expiry
UP bid/ask
DOWN bid/ask
spread
liquidity
order book
trades
time remaining
final resolution
```

## Settlement / Reference Data

Collect enough information to reconstruct the market outcome correctly.

The exact settlement mechanism should be verified rather than assumed.

## Data Engineering Topics

Learn:

- REST APIs;
- WebSockets;
- continuous data ingestion;
- reconnection;
- retries;
- duplicate prevention;
- raw vs processed storage;
- timestamp synchronization;
- data validation;
- database design where necessary.

## Exploratory Data Analysis

Before ML training, investigate questions such as:

```text
distance from strike vs outcome probability

time remaining vs uncertainty

volatility vs reversal rate

momentum vs continuation probability

strike crossing frequency vs prediction difficulty

Polymarket implied probability vs actual outcome frequency
```

The student should actively search for evidence both **supporting and contradicting** the original trading hypothesis.

Relevant statistical concepts should be learned while performing these investigations:

- distributions;
- correlation;
- confidence intervals;
- sampling;
- hypothesis testing;
- statistical significance;
- practical significance.

## Deliverable

A reproducible research dataset plus an EDA report containing:

- observed patterns;
- hypotheses that appear promising;
- hypotheses that appear wrong;
- suspicious correlations;
- potential predictive features;
- potential sources of data leakage;
- remaining questions.

---

# Phase 3 — Baselines and First Machine Learning Models

## Objective

Establish how difficult the prediction problem actually is before introducing sophisticated models.

Start with non-ML baselines.

Possible baselines include:

```text
Always predict majority outcome

Current BTC position relative to strike

Short-term momentum continuation

Simple trend rule

Polymarket implied probability
```

A machine-learning model should demonstrate value relative to meaningful baselines, not merely achieve an impressive-looking accuracy number.

## First ML Model

Begin with Logistic Regression.

Potential feature vector:

```text
return_30s
return_1m
return_3m
realized_volatility
distance_from_strike
normalized_distance_from_strike
time_remaining
volume_change
price_range
strike_crossing_count
momentum_consistency
bid_ask_spread
order_book_imbalance
Polymarket_implied_probability
```

Target:

```text
1 = UP resolves
0 = DOWN resolves
```

Output:

```text
P(UP)
```

Rather than merely:

```text
UP
```

## Learning Topics

Learn:

- supervised learning;
- features and labels;
- logistic regression;
- loss functions;
- regularization;
- training and validation;
- overfitting;
- underfitting;
- feature scaling;
- model interpretation.

## Time-Series Validation

This section is critical.

The instructor must specifically teach:

- chronological train/test separation;
- look-ahead bias;
- future leakage;
- overlapping observations;
- feature timestamp correctness;
- target leakage;
- preprocessing leakage.

Random train/test splitting should not be used blindly for financial time-series data.

## Deliverable

A baseline comparison and first properly validated probability model.

The student should be able to explain both why the model works and why it may fail.

---

# Phase 4 — Model Evaluation, Probability Calibration, and Market Regimes

## Objective

Move beyond simple accuracy and determine **when the model can actually be trusted**.

Evaluate metrics such as:

```text
Accuracy
Precision
Recall
ROC-AUC
Log Loss
Brier Score
Calibration Curve
Confusion Matrix
```

Probability calibration is especially important.

If the model repeatedly predicts:

```text
P(UP) = 70%
```

then roughly 70% of comparable events should resolve Up if the probability estimate is well calibrated.

This matters because trading decisions will eventually compare the model's probability with Polymarket prices.

---

## Regime Analysis

Now test the original regime hypothesis formally.

Initially, regimes can be defined using transparent measurable conditions instead of immediately using another ML model.

Possible variables:

```text
trend strength
volatility
directional consistency
distance from strike
strike crossing frequency
momentum persistence
```

Possible regimes:

```text
Strong directional trend
Moderate trend
Equilibrium
High-volatility chop
Countertrend
```

Then evaluate model performance separately.

For example:

| Regime         | Accuracy | Calibration | Trading Potential |
| -------------- | -------: | ----------: | ----------------: |
| Strong Trend   |        ? |           ? |                 ? |
| Moderate Trend |        ? |           ? |                 ? |
| Equilibrium    |        ? |           ? |                 ? |
| Volatile Chop  |        ? |           ? |                 ? |

These values must come from the data rather than expectations.

The system may eventually discover conditions where:

```text
Model has edge
→ prediction allowed
```

and:

```text
Model historically performs poorly
→ NO TRADE
```

Later, techniques such as clustering or regime-switching models may be investigated if justified.

## Deliverable

A model evaluation and regime report answering:

> Under which conditions does our model perform meaningfully better or worse?

---

# Phase 5 — Improve the Model and Engineer Better Features

## Objective

Determine whether stronger ML methods and richer market information produce a genuine improvement.

Possible models:

```text
Decision Trees
Random Forest
Gradient Boosting
XGBoost
LightGBM
CatBoost
```

Every stronger model must be compared against the simpler baseline.

The key question is:

> Does additional complexity improve unseen-data performance enough to justify itself?

## Feature Engineering

Explore features based on actual hypotheses.

### Momentum

```text
short-term returns
trend persistence
price acceleration
breakout strength
```

### Volatility

```text
realized volatility
range expansion
volatility change
```

### Strike Relationship

```text
absolute distance from strike
distance / volatility
distance / expected remaining movement
strike-crossing frequency
```

### Market Microstructure

```text
bid/ask spread
order-book imbalance
trade imbalance
liquidity
depth
aggressive buying/selling
```

### Time

```text
seconds until settlement
time × distance interaction
time × volatility interaction
```

The instructor should discourage adding indicators merely because they are popular.

Features should preferably have either:

- economic reasoning;
- market-structure reasoning;
- statistical justification;
- or experimental evidence.

## Experiment Tracking

Every important experiment should record:

```text
experiment_id
dataset_version
features
model
hyperparameters
training_period
validation_period
test_period
metrics
notes
```

This introduces reproducible ML experimentation.

## Deliverable

A documented model comparison showing:

- which features help;
- which features do not;
- which model generalizes best;
- whether the original hypothesis remains supported.

---

# Phase 6 — Convert Predictions Into a Trading Strategy and Backtest It

## Objective

Separate **prediction quality** from **trading profitability**.

A correct model prediction should not automatically create a trade.

Suppose:

```text
Model P(UP) = 0.78
UP ask      = $0.61
```

There may be an opportunity.

But:

```text
Model P(UP) = 0.78
UP ask      = $0.77
```

may offer little or no useful edge.

The decision pipeline should move toward:

```text
Model Probability
        ↓
Executable Market Price
        ↓
Estimated Edge
        ↓
Model Confidence
        ↓
Regime Filter
        ↓
Liquidity / Spread
        ↓
Risk Rules
        ↓
TRADE or NO TRADE
```

## Learn

- expected value;
- market-implied probability;
- edge;
- decision thresholds;
- transaction costs;
- bid/ask spread;
- slippage;
- execution risk;
- uncertainty;
- position sizing basics.

## Realistic Backtesting

Backtests must only use information that existed at the simulated decision time.

Avoid assumptions such as:

```text
perfect fills
zero latency
zero spread
unlimited liquidity
future information
```

Where possible, model:

- actual bid/ask;
- fees;
- slippage;
- execution delay;
- missed fills;
- position size;
- available liquidity.

## Evaluation

Evaluate:

```text
total return
expected return per trade
hit rate
drawdown
number of trades
risk-adjusted performance
performance by regime
performance by confidence
performance by time remaining
```

A particularly important question is:

> Does profitability come from a repeatable pattern, or from a small number of lucky trades?

## Walk-Forward Testing

Introduce sequential evaluation such as:

```text
Train → Jan–Mar
Validate → April
Test → May

Move forward

Train → Feb–Apr
Validate → May
Test → June
```

This introduces:

- changing market conditions;
- non-stationarity;
- concept drift;
- model retraining.

## Deliverable

A realistic backtesting framework and documented trading-strategy evaluation.

---

# Phase 7 — Real-Time Paper Trading and Production ML

## Objective

Move from historical research into a continuously operating system without risking real capital.

Architecture may evolve toward:

```text
Market Data Collectors
        ↓
Raw Data Storage
        ↓
Feature Pipeline
        ↓
Model Inference
        ↓
Regime / Strategy Engine
        ↓
Risk Engine
        ↓
Simulated Execution
        ↓
Monitoring + Database
```

## Shadow / Paper Trading

Run the complete pipeline against live markets.

The system should generate exactly what it would have done with real capital:

```text
prediction
probability
market price
trade/no-trade decision
position size
simulated order
simulated fill
final result
P&L
```

This makes it possible to compare historical backtests with real operational behavior.

## Software Engineering Topics

Learn:

- modular architecture;
- configuration;
- tests;
- logging;
- Docker;
- deployment;
- scheduling;
- process supervision;
- databases;
- model versioning;
- monitoring.

## Reliability

A 24/7 system must safely handle:

```text
API outages
WebSocket disconnects
stale market data
clock/timestamp problems
missing observations
duplicate messages
database failure
model failure
partial data
unexpected market state
```

The preferred behavior during uncertainty should usually be:

```text
NO TRADE
```

For example:

```text
IF market data is stale:
    NO TRADE

IF model inference fails:
    NO TRADE

IF settlement/reference source is unavailable:
    NO TRADE
```

## Deliverable

A continuously operating paper-trading system with complete logging and monitoring.

---

# Phase 8 — Risk Management, Live-Readiness, and Advanced ML

## Objective

Determine whether the project has sufficient evidence and operational maturity to justify limited real trading.

Prediction and risk management must remain separate.

The risk engine should eventually define rules such as:

```text
maximum position size
maximum total exposure
maximum daily loss
minimum estimated edge
minimum liquidity
maximum acceptable spread
model-confidence requirements
emergency kill switch
```

A confident model must not be allowed unlimited exposure.

## Live-Readiness Review

Before considering automated execution, review:

### Statistical Evidence

- Does the model outperform meaningful baselines?
- Is performance stable out of sample?
- Is probability calibration acceptable?
- Is the edge present across enough independent samples?

### Trading Evidence

- Does the edge survive spread, fees, slippage, and latency?
- Does paper trading behave similarly to backtesting?
- Is performance overly dependent on one particular regime?

### Engineering Evidence

- Can the system recover safely from failures?
- Are all decisions logged?
- Can trading be stopped immediately?
- Can stale data accidentally generate an order?
- Can duplicate orders occur?

Only after passing these checks should small-capital execution even be considered.

---

## Advanced ML

Advanced methods are intentionally placed at the end.

Potential topics:

```text
LSTM / GRU
Temporal Transformers
Ensemble models
Online learning
Bayesian methods
Regime-switching models
Representation learning
Reinforcement learning
```

Before adopting one, the instructor and student must answer:

> What limitation in the existing system are we trying to solve?

If the answer is merely:

> "This model is more advanced."

then it should not be introduced yet.

---

# Final Learning Outcome

At the end of the project, the student should understand the complete lifecycle:

```text
Hypothesis
    ↓
Data Collection
    ↓
Data Analysis
    ↓
Feature Engineering
    ↓
Machine Learning
    ↓
Validation
    ↓
Regime Analysis
    ↓
Probability Estimation
    ↓
Trading Decision
    ↓
Backtesting
    ↓
Paper Trading
    ↓
Production Deployment
    ↓
Monitoring
    ↓
Continuous Improvement
```

Project success should not be defined solely as whether the bot makes money.

Success has several levels:

### Learning Success

The student can independently understand and build an end-to-end ML system.

### Research Success

The student can determine scientifically whether the original market-regime hypothesis is supported.

### Predictive Success

The model shows stable out-of-sample predictive power.

### Trading Success

That predictive advantage survives real market prices and execution costs.

### Production Success

The system can operate continuously and safely.

It remains a successful learning and research project even if the final conclusion is:

> **No sufficiently reliable trading edge was found.**

Finding that result correctly is better than creating a profitable-looking system through overfitting, leakage, or unrealistic backtesting.
