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

## Balanced graph dataset

A balanced graph-feature dataset was created from graph_features.csv.

The smallest valid city group was Sarajevo with 476 patches.

We sampled 476 patches from each city.

Balanced dataset size:

**3,808 patches**

Balanced patch count by city:

| City | Patches |
|---|---:|
| Barcelona | 476 |
| Chicago | 476 |
| Lisbon | 476 |
| London | 476 |
| Manhattan | 476 |
| Paris | 476 |
| Sarajevo | 476 |
| Tokyo | 476 |

Output file:

**data/processed_global/graph_features_city_balanced.csv**

Reason:

The original graph feature dataset was unbalanced by city.

Balancing reduces the risk that cities with more valid patches dominate the EDA or model.