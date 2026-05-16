# EDA Graph Histograms

## Purpose

This note explains the graph-feature histograms created for the city-balanced dataset.

The goal is to check whether our graph features are usable before predicting **street-network entropy**.

A histogram shows how many patches fall into each value range.

This helps us see:

- if a feature has useful variation
- if a feature is mostly zero
- if a feature has extreme outliers
- if a feature may need filtering
- if a feature should be kept for modeling

## Dataset used

The histograms were made from the city-balanced graph dataset:

**graph_features_city_balanced.csv**

This dataset contains:

- 8 cities
- 476 patches per city
- 3,808 total patches

The city-balanced dataset reduces the risk that one city dominates the analysis.

## Why histograms matter

Histograms are an early **EDA** step.

**EDA** means Exploratory Data Analysis.

Plain meaning:

We look at the dataset before modeling to understand what is inside it.

For this project, histograms help answer:

Are the graph features clean enough to use?

Do they describe different types of street networks?

Do they contain values that may confuse the model?

The model will later try to learn:

**graph features → entropy**

If a graph feature has no variation, the model cannot learn from it.

If a feature has extreme outliers, it may distort the model.

If a feature has a clear spread, it may be useful.

---

# Feature-by-feature notes

## beta_index

**Plain meaning:**  
How many street connections exist compared to street points.

Higher values suggest:

- more connected networks
- more route options
- more grid-like structure

Lower values suggest:

- fewer connections
- more tree-like networks
- less connected structure

**What the histogram shows:**  
The distribution looks healthy.

Most patches are around the middle range.

There are fewer patches at the low and high ends.

**Interpretation:**  
This feature has useful variation.

It is not broken.

It can help describe street-network connectivity.

**Decision:**  
Keep.

---

## cv_edge_length

**Plain meaning:**  
How uneven the street segment lengths are.

Low values suggest:

- similar street segment lengths
- more regular block structure

High values suggest:

- mixed short and long segments
- more irregular street structure

**What the histogram shows:**  
Most patches are in a moderate range.

There is a long tail toward higher values.

Some patches have unusually high variation.

**Interpretation:**  
Most patches have moderate edge-length variation.

Some patches are much more irregular.

The high values may be real, but they need checking.

**Decision:**  
Keep, but review outliers.

---

## dead_end_ratio

**Plain meaning:**  
How many streets stop without continuing.

Higher values suggest:

- more dead ends
- more fragmented networks
- less connected street fabric

Lower values suggest:

- fewer dead ends
- more continuous networks
- stronger street connectivity

**What the histogram shows:**  
This feature is not all zero.

Most patches have a moderate dead-end ratio.

Some patches have high dead-end ratios.

**Interpretation:**  
This is useful.

Earlier, we were worried this feature was useless.

The new balanced dataset shows that it has variation.

**Decision:**  
Keep.

---

## intersection_density

**Plain meaning:**  
How many street decision points exist inside a patch.

Higher values suggest:

- dense street networks
- many intersections
- compact urban fabric

Lower values suggest:

- sparse street networks
- larger blocks
- less urban intensity

**What the histogram shows:**  
Most patches are in a moderate density range.

There is a long tail toward very high values.

Some patches are extremely dense.

**Interpretation:**  
This feature is useful, but skewed.

The high-density patches may be real dense urban cores.

They may also be outliers or artifacts.

**Decision:**  
Keep, but inspect high values.

---

## mean_edge_length

**Plain meaning:**  
The average length of street segments.

Low values suggest:

- short blocks
- dense intersections
- fine-grain urban fabric

High values suggest:

- long blocks
- fewer intersections
- larger-scale street structure

**What the histogram shows:**  
Most patches have relatively short average edge lengths.

There is a long tail toward longer street segments.

A few patches have very long average edge lengths.

**Interpretation:**  
Most patches represent fine-grain urban fabric.

Very high values may represent:

- large blocks
- waterfront edges
- parks
- sparse urban areas
- edge conditions

**Decision:**  
Keep, but check very high values.

---

## mean_node_degree

**Plain meaning:**  
Average street connectivity at each node.

Higher values suggest:

- more connected intersections
- more 4-way crossings
- stronger grid logic

Lower values suggest:

- more dead ends
- more 3-way intersections
- less connected networks

**What the histogram shows:**  
The distribution looks healthy.

Most patches sit in a clear middle range.

There are no obvious broken values.

**Interpretation:**  
This is a stable and useful graph feature.

It gives a general measure of street-network connectivity.

**Decision:**  
Keep.

---

## meshedness

**Plain meaning:**  
How much the street network forms loops.

High values suggest:

- more closed loops
- more route alternatives
- more grid-like networks

Low values suggest:

- tree-like networks
- fewer loops
- more fragmented streets

**What the histogram shows:**  
Most patches have low-to-medium meshedness.

There is a visible group near zero.

**Interpretation:**  
This feature is useful, but the near-zero group needs attention.

Near-zero patches may be:

- weakly connected patches
- sparse areas
- city-edge patches
- patches with little loop structure

**Decision:**  
Keep, but inspect patches near zero.

---

## network_density

**Plain meaning:**  
How much street length exists inside a patch.

Higher values suggest:

- dense street fabric
- compact urban structure
- many streets per area

Lower values suggest:

- sparse networks
- open areas
- less urbanized patches

**What the histogram shows:**  
Most patches are in a moderate range.

There is a long tail toward high network density.

A few patches are much denser than the rest.

**Interpretation:**  
This feature is useful.

It captures urban intensity.

It may overlap with **intersection_density**.

**Decision:**  
Keep, but compare with intersection_density.

---

## proportion_3way

**Plain meaning:**  
The proportion of 3-way intersections.

Higher values suggest:

- many T-junctions
- branching street logic
- possibly organic or hierarchical fabric

Lower values suggest:

- fewer T-junctions
- more grid-like structure
- more 4-way intersections

**What the histogram shows:**  
The distribution is balanced.

Most patches sit around the middle range.

There is clear variation.

**Interpretation:**  
This is useful.

It may help distinguish branching fabrics from grid fabrics.

**Decision:**  
Keep.

---

## proportion_4way

**Plain meaning:**  
The proportion of 4-way intersections.

Higher values suggest:

- more cross intersections
- stronger grid logic
- more planned street structure

Lower values suggest:

- fewer cross intersections
- more irregular or branching structure

**What the histogram shows:**  
Many patches have low 4-way proportions.

There is a long tail toward higher values.

Some patches have much stronger 4-way structure.

**Interpretation:**  
This feature is very relevant for entropy.

Grid-like areas should usually have stronger 4-way intersection patterns.

Irregular fabrics may have fewer 4-way intersections.

**Decision:**  
Keep.

This is one of the strongest graph features.

---

# Main conclusions

## Features that look healthy

These features have clear variation and no obvious failure:

- beta_index
- mean_node_degree
- proportion_3way
- proportion_4way
- dead_end_ratio

## Features with possible outliers

These features are useful but have long tails:

- intersection_density
- network_density
- mean_edge_length
- cv_edge_length

These should be checked before modeling.

## Feature to inspect carefully

**meshedness** should be reviewed because it has a visible group near zero.

This may represent real sparse patches or weak network structure.

---

# What the histograms prove

The histograms show that our graph features are not empty or flat.

They have enough variation to continue with EDA.

This means the graph-feature dataset is usable for the next analysis step.

The histograms also show which features may need filtering or closer inspection.

---

# What the histograms do not prove

Histograms only show one feature at a time.

They do not show whether a feature predicts entropy.

They do not show relationships between features.

They do not show whether cities cluster separately.

So the next steps are:

1. create a correlation matrix
2. compare each graph feature with entropy
3. make histograms split by city
4. make PCA plots colored by city
5. make PCA plots colored by entropy

---

# Support-session explanation

We created histograms for the city-balanced graph features.

These plots help us check if each feature is usable before modeling.

The main finding is that the graph features have real variation.

Dead-end ratio is not useless anymore.

Proportion 4-way, proportion 3-way, mean node degree, beta index, and meshedness look useful for describing street-network structure.

Some density features have outliers, especially intersection density and network density.

The next step is to check whether these graph features actually relate to **entropy_normalized**.