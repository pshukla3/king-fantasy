# King Fantasy

NFL fantasy football projections, built from measured signal rather than
tuned by feel. Live at **https://kingfantasyfootball.com**

Every weight in the model was tested for year-over-year persistence before
being used. Signals that did not repeat were dropped and are documented
below rather than quietly discarded.

## What it does

- **Projections** for every player, per week, from 20,000 Monte Carlo
  simulations per game — adjusted for opponent, home/away and Vegas totals
- **Rankings** with value over replacement, measured by filling every
  starting slot league-wide rather than assuming a replacement level
- **League sync** (Sleeper) — matchups, standings, playoff odds from
  20,000 season simulations off actual records, with an all-play luck metric
- **Mock draft** against CPUs that draft to the board, snake/linear/3RR
- **Start/sit** on opponent-adjusted weekly projections
- **Trade calculator** scoring both sides independently
- **Accuracy report** — error rates published in full, including the models
  that lost

## How projections work

Components are projected separately, then simulated — never points directly.

Each component is shrunk toward the league mean by its *measured*
reliability, using Spearman-Brown:

    k = n_eff * r / (1 + (n_eff - 1) * r)

Where `r` is the season-to-season correlation of that component. Measured
values, from eleven seasons of play-by-play:

| Component | r | Used |
|---|---|---|
| Target share | 0.827 | yes |
| Rush attempts (QB) | 0.463 | yes |
| Pass attempts | 0.394 | yes |
| aDOT | 0.333 | yes |
| Catch rate | 0.275 | yes |
| Yards per reception | 0.085 | no |
| Touchdown rate | ~0.00 | no — regressed to baseline |

Touchdown rate does not persist year over year. It is regressed toward a
positional baseline rather than extrapolated, which is why this model is
less excited than most about last week's two-touchdown game.

Quarterbacks are split into passing and rushing. Rushing points persist at
r = 0.315, passing at r = 0.119 — that gap is most of why dual-threat
quarterbacks separate from pocket passers once shrinkage is applied.

## Measured accuracy

- Week 10, 263 players: **mean error +0.65**, mean absolute error **5.01**
- Season-long projections vs actual ppg, 304 players with 5+ games:
  **mean error +0.145**, mean absolute error **2.615**

The model is close to unbiased. Its weakness is dispersion, not direction.

## What it does not do

- **There is no fitted model.** Every parameter is explicitly derived from
  measured reliabilities. Calling this machine learning would be wrong.
- **Kicker projections are near the noise floor.** Week-to-week kicker
  scoring correlates at r = 0.040. The model beats a flat league average by
  2.6% on RMSE. That is close to the ceiling for the position.
- **No defensive player projections.**
- Only Sleeper league sync is live. ESPN and Yahoo are in progress.

## Pipeline

Raw play-by-play (nflreadpy, 11 seasons) -> component parameters per
player -> share normalisation -> 20k simulations per player per week ->
replacement level and VORP -> injury and availability layer -> static site.

Roughly 180 ordered scripts, run by `deploy.sh`, publishing to Netlify.

## Stack

Python (polars, pandas, numpy), nflreadpy, vanilla JS, Netlify Functions,
Supabase auth.
