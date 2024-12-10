# Malazan Network Analysis Report

## Introduction

> - Bugg's Construction will be the first major enterprise to collapse.   
> - And how many will it drag down with it?
> - No telling. Three, maybe four.
> - I thought you said there was no telling.
> - So don't tell anyone.
> - Good idea, Bugg.
>
> ― Steven Erikson, The Malazan Book of the Fallen

In this Network Analysis of the first 9 books (out of 10) of the Malazan Book of the Fallen I am analysing
the interaction Graph between characters from the Network Analysis perspective. It's ever more interesting to do that
for complexity of this book causes nothing but awe.

**Spoiler Alert: there are many spoilers :)**

## Network Summary
[Link to Cosmograph (use files from /data/processed to draw a Graph).](https://cosmograph.app/run/)
![SVG Image](figures/gephi_graph_atlas_layout.svg)

- **Data Collection & Preprocessing Process**:
    - Characters co-occurrence and POV count of words were taken from
      this [GitHub repo](https://github.com/visuelledata/malazannetwork/)
    - I have manually corrected some mistakes in the datasets above
    - Then I've parsed some of the Malazan-wiki pages in order to:
      a) Get extra information about characters in order to be able to differentiate characters based on their gender,
      race, affiliation;
      b) Using regEx parse attributes, which were mentioned in  (a), from info Dramatis Personea characters description;
      c) Enrich characters data with first (a), and when not enough information was found then already (b) for I trust
  Malazan Wiki more than my regEx;
    - Removed edges where number of alleged contacts was lower than 5
    - Unfortunately, I had to remove Hood and Maybe from the network because the name Hood is a part of colloquial
  expressions ("Hood's breath", "Hood's balls", "Hood take me", etc.) and the word `maybe` oftentimes stand in the beginning of the sentence.
- **Graph type**: undirected homogeneous weighted
- **Nodes attributes**: `gender`, `race`, `affiliation`, `warrens`, `occupation`, `POV words count`,
  `Number of books character appeared in`
- **Edges attributes**: `Number of times personages interacted`. To be more specific, it's the number of times names
  stood close to each other in the text, what we, with some error, may interpret as how many times they interacted
- **Number of Connected Components**: ${connected_components_number}
- **Greatest Connected Component Size, share**: ${greatest_connected_component_size_ratio}
- **Diameter (largest CC)**: ${network_diameter}
- **Radius (largest CC)**: ${network_radius}
- **Global Clustering Coefficient**: ${global_clustering}
- **Average Clustering Coefficient**: ${avg_clustering}
  <details>
  <summary>Click to show plot</summary>

  ![Clustering Coefficient Histogram](figures/clustering_histogram.png)
  </details>

- **Average Shortest Path Length (largest CC)**: ${avg_shortest_path_length}
  <details>
  <summary>Click to show plot</summary>

  ![Shortest Paths Histogram](figures/shortest_paths_histogram.png)
  </details>

- **Power Degree Distribution**
  <details>
  <summary>Click to show plots</summary>

  ![Power Degree Histogram](figures/power_degree_histogram.png)
  ![Power Degree ECDF](figures/power_degree_ecdf.png)
  ![Power Degree Distribution](figures/degree_distribution.png)
  </details>

- **Results Interpretation:** Non-surprisingly, it can be seen from *Average Clustering Coefficient* and the histogram of
*Local Clustering Coefficients* that the characters form the largest connected component are well-connected to each other.
Nonetheless, there are many personae, as it can be seen from the *Power Degree Distribution*, that have only 1 or 2 connections.
Those are largely either short-lived characters or briefly-mentioned ones, names of which I can hardly recognize.

## Structural Analysis
- **Network Comparison with Randomly Generated Graphs.**
  <details>
  <summary>Click to show plots</summary>

  ![Random Networks Comparison](figures/random_networks_comparison.png)
  ![Random Networks Comparison](figures/random_networks_summary.png)
  </details>
- **Centralities**:
  <details>
  <summary>For reference here is POV words count for every character</summary>
  
  ![Bar Plot Top POV Personae](figures/bar_plot_top_pov_centrality.png)
  %{table_top_pov_centrality}
  </details>

  <details>
  <summary>Degree Centrality</summary>

  ![Bar Plot Top Personae by Degree Centrality](figures/bar_plot_top_degree_centrality.png)
  %{table_top_degree_centrality}
  </details>

  <details>
  <summary>Closeness Centrality</summary>

  ![Bar Plot Top Personae by Closeness Centrality](figures/bar_plot_top_closeness_centrality.png)
  %{table_top_closeness_centrality}
  </details>
  
  <details>
  <summary>Betweenness Centrality</summary>

  ![Bar Plot Top Personae by Betweenness Centrality](figures/bar_plot_top_betweenness_centrality.png)
  %{table_top_betweenness_centrality}
  </details>

  <details>
  <summary>Katz Centrality</summary>

  ![Bar Plot Top Personae by Katz Centrality](figures/bar_plot_top_eigenvector_centrality.png)
  %{table_top_eigenvector_centrality}
  </details>
  
- **Page-Rank**:
  - <details>
    <summary>Click to expand table</summary>

    ![Bar Plot Top Personae by Page Rank](figures/bar_plot_top_pagerank_centrality.png)
    %{table_top_pagerank_centrality}
    </details>
  - *Correlation comparison of centralities and prestige*
    <details>
    <summary>Click to show plots</summary>
    
    ![Pair Plot Centralities and PageRank](figures/pairplot_centralities_and_pagerank.png)
    ![Corr Matrix Centralities and PageRank](figures/corr_centralities_and_pagerank.png)
    </details>

- **Assortative Mixing**:
  <details>
  <summary>Gender</summary>

  ![Bar Plot Top Personae by Page Rank](figures/heatmap_assortativity_mixing_gender.png)
  </details>
  <details>
  <summary>Race</summary>

  ![Bar Plot Top Personae by Page Rank](figures/heatmap_assortativity_mixing_race_first.png)
  </details>
  <details>
  <summary>Affiliation</summary>

  ![Bar Plot Top Personae by Page Rank](figures/heatmap_assortativity_mixing_affiliation_first.png)
  </details>

- **Node structural equivalence/similarity**:
  <details>
  <summary>Jaccard Similarity</summary>
  
  ![Heatmap with Nodes Structural Similarity](figures/heatmap_nodes_structural_similarity_jaccard.png)
  </details>
  <details>
  <summary>Cosine Similarity</summary>

  ![Heatmap with Nodes Structural Similarity](figures/heatmap_nodes_structural_similarity_cosine.png)
  </details>

- **Edges weights between top nodes**
  <details>
  <summary>Click to show plot</summary>

  ![Heatmap with Edge Weights](figures/heatmap_edges_weights.png)
  </details>

**Results Interpretation:**

Interestingly, among top 3 personae ranked by *centrality measures*, only Fiddler is also in the top of POV words count.
The reason for that lies in the way Steven Erikson wanted us to perceive Quick Ben and Tavore. The former masterminded
many convergences without us realising that (due to the lack of POV), while the latter was (and is) an unsolved mistery
(we did not really get to know her well enough; and that was purposeful).
Nevertheless, these two are of utmost importance for the events in the Book and thus they have communicated with the
great number of other people. What made them different from, say Anomander Rake or Shadowthrone (Ammanas), whose role
was instrumental as well, was the fact that they underwent more targeted actions and communications, while Tavore and
Quick Ben were always in the middle of something themselves (apart from being a part of the big and highly-connected army).


It is also amusing how *Page-Rank* algorithm pushed Anomander Rake, Brys Beddict, and brother Sengars to the top, though
truth be told, I expected to see Ganoes Paran and Tehol Beddict here as well (perhaps they would've appeared in the
top had we considered the 10th book). The reason for this reshuffle is that those characters are big shots that
communicated actively with the other big shots. All of them are at the top of some organisations.
Other than that Centralities are mostly highly-correlated.

Speaking of *Assortative Mixing*, we can well see that were a lot of intergender communications (assortativity coefficient
is around 0), which is to be expected, given Steven's desire to make the Book free of prejudices (that is, without
discrimination based on gender, race, skin color, etc.). *Race Mixing Matrix* shows us that most of the contacts are
between Malazans. In the end, they are the central history-makers. The same situation can be observed in *Affiliation
Mixing Matrix*.

Brushing upon *node structural equivalence* (using cosine similarity), it can be well seen that our favorite Malazans
(Quick Ben, Fiddler, Gesler, Whiskeyjack, Tavore) are quite similar to one another. No wonder, given that they crossed
the continents and the seas hand in hand (being thus in the same milieu and forming common bonds of friendship).



## Community Detection
<details>
<summary>Clique Size Distribution</summary>
%{table_clique_size_distribution}
</details>

<details>
<summary>K-cores Visualization</summary>

![SVG Image](figures/gephi_graph_atlas_layout_core_number.svg)
</details>

<details>
<summary>K-percolation community detection algorithm</summary>

![SVG Image](figures/gephi_graph_atlas_layout_k_percolation.svg)
</details>

<details>
<summary>Louvain community detection algorithm</summary>

![SVG Image](figures/gephi_graph_atlas_layout.svg)
</details>

**Results Interpretation:**

*Louvain community detection* algorithm appears to work really well in case of the Malazan Book (Modularity: 0.5628).

Take a look:

- Community 0 (Darujhistan Heroes): Apsalar, Kruppe, Cutter, Baruk, Rallick Nom, Murillio, etc.
- Community 3: Olar Ethil, Cotillion, Silchas Ruin, Kilmandaros, Menandore, Clip, Sechul Lath, Aparal Forge, Korabas, and others.
  As we can see, this community is comprised mostly by characters in the status of legends that got well acquainted with
  each other over the millennia.
- Community 4: consists of Fokrul Assails only.
- Community 7: mostly Malazans (Bridgeburners) and their close allies.
- Community 9: other Malazan heavies and marines.
- Community 10: main actors on the Lether continent (Tiste Edures and Letherii).




## References
<details>
<summary>Expand references</summary>
  Erikson, S. (1999). *Gardens of the Moon*. London: Bantam Press.
  
  Erikson, S. (2000). *Deadhouse Gates*. London: Bantam Press.
  
  Erikson, S. (2001). *Memories of Ice*. London: Bantam Press.
  
  Erikson, S. (2002). *House of Chains*. London: Bantam Press.
  
  Erikson, S. (2004). *Midnight Tides*. London: Bantam Press.
  
  Erikson, S. (2006). *The Bonehunters*. London: Bantam Press.
  
  Erikson, S. (2007). *Reaper's Gale*. London: Bantam Press.
  
  Erikson, S. (2008). *Toll the Hounds*. London: Bantam Press.
  
  Erikson, S. (2009). *Dust of Dreams*. London: Bantam Press.
  
  Cedarosaurus. (2018, November 30). Main series character POV data [Reddit post]. r/Malazan.  
  https://www.reddit.com/r/Malazan/comments/a1ukxk/main_series_character_pov_data/
  
  Malazan Wiki. (n.d.). *Malazan Wiki*. Fandom.  
  https://malazan.fandom.com/wiki/Malazan_Wiki
  
  visuelledata. (n.d.). *malazannetwork*. GitHub.  
  https://github.com/visuelledata/malazannetwork/

  Bastian, M., Heymann, S., & Jacomy, M. (2009). Gephi: An open source software for exploring and manipulating networks. *International AAAI Conference on Weblogs and Social Media*.
 </details> 