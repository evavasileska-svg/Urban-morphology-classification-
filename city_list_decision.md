# City List Decision

## Project context

Our project predicts **street-network entropy** for **500m × 500m urban patches**.

The target is **entropy_normalized**.

The cities are not the prediction target.

The cities are the source of urban patches.

Each city gives us multiple patch samples.

Each patch has:

- graph features
- terrain features
- building features
- one entropy value

## Why we need a clear city list

We need a city list that supports the dataset.

We are not only collecting countries.

We are collecting different **urban conditions**.

The city list should help us test whether entropy prediction works across different street-network patterns.

## First pilot list

We start with **8 cities**.

This keeps the dataset manageable.

It also gives enough variation for early testing.

## Selected cities

1. **Barcelona, Spain**
2. **Paris, France**
3. **London, United Kingdom**
4. **Lisbon, Portugal**
5. **Sarajevo, Bosnia and Herzegovina**
6. **Manhattan, New York, USA**
7. **Chicago, Illinois, USA**
8. **Tokyo, Japan**

## City roles

### Barcelona, Spain

**Role:** regular grid and Eixample-style urban order.

**Why included:** Barcelona gives a clear example of ordered street-network structure.

**Expected entropy logic:** lower entropy in regular grid areas.

**Risk:** not all Barcelona follows the Eixample grid.

---

### Paris, France

**Role:** dense historical fabric with radial and boulevard logic.

**Why included:** Paris mixes historical irregularity with planned axes.

**Expected entropy logic:** mixed entropy depending on district.

**Risk:** different districts may behave very differently.

---

### London, United Kingdom

**Role:** irregular historical street network.

**Why included:** London gives a strong example of organic street growth.

**Expected entropy logic:** higher entropy in irregular fabric.

**Risk:** the city is large and heterogeneous.

---

### Lisbon, Portugal

**Role:** hilly terrain with irregular street adaptation.

**Why included:** Lisbon helps test the link between terrain and street entropy.

**Expected entropy logic:** higher entropy where streets follow topography.

**Risk:** terrain may dominate the interpretation.

---

### Sarajevo, Bosnia and Herzegovina

**Role:** valley and hilly condition with constrained urban growth.

**Why included:** Sarajevo helps test terrain-constrained urban form.

**Expected entropy logic:** irregular networks may appear near steep terrain.

**Risk:** OpenStreetMap data quality may vary.

---

### Manhattan, New York, USA

**Role:** strong orthogonal grid and low-entropy benchmark.

**Why included:** Manhattan gives a clear reference for ordered street direction.

**Expected entropy logic:** low entropy due to dominant grid directions.

**Risk:** Manhattan’s scale differs from European grids.

---

### Chicago, Illinois, USA

**Role:** flat terrain with strong grid structure.

**Why included:** Chicago gives a second grid example.

**Expected entropy logic:** low entropy in regular grid areas.

**Risk:** it may be similar to Manhattan.

---

### Tokyo, Japan

**Role:** dense mixed network with complex local patterns.

**Why included:** Tokyo tests the method outside European and American grids.

**Expected entropy logic:** mixed or higher entropy in complex local fabrics.

**Risk:** data download and processing may be heavy.

## Urban conditions covered

The pilot list covers:

- regular grid networks
- irregular historical fabrics
- hilly terrain cities
- flat terrain cities
- dense urban cores
- mixed street-network structures
- European and non-European examples

## Dataset design logic

The city list is selected by **urban condition**, not only by geography.

The goal is to compare different street-network structures.

The city should help us understand entropy variation.

## Main risk

The model may learn **city identity** instead of entropy-related spatial structure.

For example, it may learn:

- this looks like Barcelona
- this looks like London
- this looks like Tokyo

Instead of learning:

- this patch has ordered street directions
- this patch has irregular street directions
- this patch has high or low entropy

## How we will control this risk

We will compare cities using:

- histograms per feature
- entropy distribution per city
- PCA plots colored by city
- spider charts per city
- feature-to-entropy plots
- city-level summary tables

## Current working decision

We keep the **8-city pilot list** for the first dataset test.

We use **500m × 500m patches** as the sample unit.

We use **entropy_normalized** as the prediction target.

We use city-level plots to check whether the patch logic makes sense.

## Open questions for support session

1. Is this 8-city list balanced enough for a first pilot?
2. Should we add more cities per urban condition?
3. Is one city per condition too weak for ML?
4. Should Manhattan be used instead of all New York City?
5. Should Tokyo be reduced to a smaller area?
6. Should we include more grid cities or more irregular cities?
7. Should terrain-driven cities be grouped separately?
8. Should entropy be interpreted at patch scale or city scale?

## One-line explanation

We selected cities by **urban condition**, not only geography, to test whether street-network entropy can be predicted across grid, irregular, hilly, dense, and mixed urban fabrics.


## Pilot download and patch generation result

The 8-city pilot graph download was successful.

The script downloaded 5 km walking-network graphs around each city center.

Patch centres were generated using 500m grid spacing.

Total patch centres generated: 11,784.

Patch count by city:

| City | Patch centres |
|---|---:|
| Barcelona | 1,600 |
| Paris | 1,600 |
| London | 1,600 |
| Lisbon | 1,184 |
| Sarajevo | 1,600 |
| Manhattan | 1,360 |
| Chicago | 1,240 |
| Tokyo | 1,600 |

Important note: this is a pilot based on 5 km radius graph downloads, not full administrative city boundaries.