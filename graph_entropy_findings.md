# Graph Entropy Findings

## Project focus

We are testing whether graph features can help explain or predict **street-network entropy**.

The target is:

**entropy_normalised**

The sample unit is:

**one 500m × 500m urban patch**

The current dataset is city-balanced.

It contains:

- 8 cities
- 476 patches per city
- 3,808 total patches

## Current dataset logic

Each patch has graph features extracted from the street network.

Each patch also has an entropy value.

The current question is:

Can graph features explain variation in street-network entropy?

This is tested before adding terrain or building features.

## Why we started with graph features

Entropy is calculated from street direction.

Graph features are the closest feature group to street-network structure.

For this reason, graph features should be tested before terrain or building features.

Terrain and building features may still help later, but they are more indirect.

## Main EDA steps completed

We completed graph-feature EDA using the notebook:

**notebooks/09_graph_feature_eda.ipynb**

The EDA included:

- graph feature histograms
- entropy distribution
- entropy by city
- entropy vs graph feature plots
- city-colored scatter plots
- correlation with entropy
- correlation matrix
- initial feature selection groups

## Key finding 1 — Entropy has useful variation

The entropy distribution is usable for regression-style analysis.

Most patches have medium-to-high entropy.

There are also lower-entropy patches.

This means the target is not flat.

The model has variation to learn from.

## Key finding 2 — City identity matters

Entropy varies strongly by city.

Chicago has lower entropy patterns.

London, Lisbon, Sarajevo, and Tokyo show higher entropy patterns.

Barcelona and Paris are more mixed.

Manhattan has a wider spread than expected.

This means city identity may influence the model.

The model may learn city-specific patterns instead of general street-network logic.

## Key finding 3 — 4-way intersections are the strongest negative feature

The strongest graph feature is:

**proportion_4way**

Correlation with entropy:

**-0.622678**

This means:

Patches with more 4-way intersections tend to have lower entropy.

This makes architectural sense.

4-way intersections usually appear in grid-like street networks.

Grid-like networks usually have fewer dominant street directions.

Fewer dominant directions mean lower entropy.

## Key finding 4 — 3-way intersections are the strongest positive feature

The strongest positive graph feature is:

**proportion_3way**

Correlation with entropy:

**+0.544645**

This means:

Patches with more 3-way intersections tend to have higher entropy.

This also makes architectural sense.

3-way intersections often appear in branching or irregular street networks.

Branching networks often have more varied street directions.

More varied street directions mean higher entropy.

## Key finding 5 — Connectivity features are useful but may be redundant

These features have moderate negative relationships with entropy:

| Feature | Correlation with entropy |
|---|---:|
| meshedness | -0.372237 |
| mean_node_degree | -0.337443 |
| beta_index | -0.337440 |

These features describe network connectivity.

They may support the same general pattern:

more connected or grid-like networks tend to have lower entropy.

However, they may also overlap with each other.

This should be checked before modeling.

## Key finding 6 — Density features are weaker

These features have weak relationships with entropy:

| Feature | Correlation with entropy |
|---|---:|
| intersection_density | +0.112974 |
| network_density | +0.016612 |

This means general street density does not explain entropy very well.

A patch can be dense and ordered.

A patch can also be dense and irregular.

So density describes urban intensity, not street direction order.

## Key finding 7 — Dead ends and edge length features are secondary

These features are weaker:

| Feature | Correlation with entropy |
|---|---:|
| dead_end_ratio | +0.087321 |
| mean_edge_length | -0.041005 |
| cv_edge_length | -0.210071 |

They may still describe useful urban conditions.

For example:

- fragmentation
- edge conditions
- irregular street grain
- parks or infrastructure corridors

But they are not primary entropy predictors.

## Main conclusion

The graph EDA suggests that **intersection type** explains entropy better than general street density.

The most important features are:

1. **proportion_4way**
2. **proportion_3way**
3. **meshedness**

The strongest project finding is:

**4-way intersections relate to lower entropy, while 3-way intersections relate to higher entropy.**

## Feature selection decision

We created three graph-feature sets for later model testing.

### 1. All graph features

This keeps all 10 graph features.

Purpose:

baseline test.

### 2. Selected graph features

This keeps the most useful and interpretable graph features.

Features:

- proportion_4way
- proportion_3way
- meshedness
- intersection_density
- dead_end_ratio
- cv_edge_length

Purpose:

reduce redundancy while keeping useful graph information.

### 3. Minimal graph features

This keeps only the clearest entropy-related features.

Features:

- proportion_4way
- proportion_3way
- meshedness

Purpose:

test whether a simple interpretable feature set is enough.

## Current risk

The strongest pattern may partly depend on city identity.

For example:

Chicago and Manhattan help form the low-entropy grid side.

London, Lisbon, Sarajevo, and Tokyo help form the high-entropy irregular side.

This means we need to test whether the relationship works globally and inside individual cities.

## Questions for support session

1. Should we run a graph-only regression model before merging terrain and building features?
2. Should we use proportion_4way and proportion_3way as the main graph features?
3. Should beta_index and mean_node_degree both be kept, or are they redundant?
4. Should weak density features be kept as controls or removed?
5. Should city be used as a categorical feature?
6. Is patch-scale entropy acceptable for the project?
7. Should we train one global model or compare city-specific models?

## Next step

Run the first graph-only regression test.

Compare:

1. all graph features
2. selected graph features
3. minimal graph features

This will test whether the graph features contain enough signal to predict entropy.