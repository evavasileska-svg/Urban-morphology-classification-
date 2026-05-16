# Graph Feature Review

## Current goal

We are checking which graph features help describe or predict street-network entropy.

The target is:

**entropy_normalized**

The sample unit is:

**one 500m × 500m urban patch**

## Graph feature extraction result

The graph feature extraction was run on the 8-city pilot dataset.

Input:

**11,784 patch centres**

Output:

**8,440 valid graph-feature patches**

Discarded:

**3,344 patches**

## City-by-city result

| City | Valid patches | Discarded patches |
|---|---:|---:|
| Barcelona | 1,091 | 509 |
| Paris | 1,466 | 134 |
| London | 1,321 | 279 |
| Lisbon | 693 | 491 |
| Sarajevo | 476 | 1,124 |
| Manhattan | 904 | 456 |
| Chicago | 931 | 309 |
| Tokyo | 1,558 | 42 |

## First observations

Tokyo has the highest number of valid patches.

Paris and London also have strong valid patch counts.

Sarajevo has the highest number of discarded patches.

Lisbon also has many discarded patches.

This may mean that some cities have less usable street-network data inside the 5 km pilot area.

It may also mean the 500m grid includes non-urban or weakly connected areas.

## Features extracted

The current graph-feature script extracts:

- n_nodes
- n_edges
- mean_node_degree
- dead_end_ratio
- proportion_3way
- proportion_4way
- intersection_density
- mean_edge_length
- std_edge_length
- cv_edge_length
- total_edge_length
- network_density
- grain_ratio
- meshedness
- beta_index

## Main risk

The valid patch count is not balanced across cities.

This may bias the dataset toward cities with more valid patches.

For example, Tokyo has 1,558 valid patches, while Sarajevo has only 476.

## Questions for support session

1. Should we balance the number of valid patches per city?
2. Should cities with many discarded patches be kept?
3. Should we reduce the 5 km radius or change the patch grid?
4. Should graph features be analyzed before terrain and building features?
5. Which graph features are most relevant to entropy?
6. Should we add orientation-specific features, such as deviation from orthogonality?
## Graph feature file quality check

The graph_features.csv file contains 8,440 valid patches and 20 columns.

All expected graph-feature columns are present.

No obvious missing columns were found.

The dataset is usable for EDA.

However, the valid patch count is not balanced by city.

Tokyo has 1,558 valid patches, while Sarajevo has 476.

This may bias the model toward cities with more valid patches.

A balanced dataset could use 476 patches per city.

This would create 3,808 samples across 8 cities.
