from collections import Counter
from pathlib import Path
from typing import Union
from loguru import logger

import numpy as np
import networkx as nx
import pandas as pd
from cdlib import algorithms
import matplotlib.pyplot as plt

from src.config import FIGURES_DIR
from src.my_utils import save_table_to_markdown


class CommunityDetectionAlgorithm:
    """
    Base class for implementing community detection algorithms on graphs.

    This class provides common functionality for community detection algorithms,
    including visualization, modularity calculation, and community printing.

    Attributes:
        graph (networkx.Graph): The input graph to be analyzed
        communities (list): List of sets, where each set contains nodes belonging to a community
        node_to_index (dict): Mapping of node labels to numeric indices
        index_to_node (dict): Mapping of numeric indices to node labels

    Methods:
        plot_communities(pos=None): Visualizes the communities with different colors
        calculate_modularity(): Returns the modularity score of the detected communities
        print_communities(): Prints the communities in a human-readable format
    """

    def __init__(self, graph: nx.Graph):
        """
        Initialize community detection algorithm with input graph.
        :param graph: NetworkX graph object to analyze
        """
        self.graph = graph
        self.communities = None
        self.node_to_index = {node: i for i, node in enumerate(self.graph.nodes())}
        self.index_to_node = {i: node for node, i in self.node_to_index.items()}

    def plot_communities(self, pos=None):
        """
        Visualize detected communities with different colors.
        :param pos: Dictionary of node positions for visualization (optional)
        :return: None
        :raises ValueError: If communities haven't been detected yet
        """
        if self.communities is None:
            raise ValueError("Run the algorithm first using run() method")

        if pos is None:
            pos = nx.spring_layout(self.graph)

        # Create color mapping for nodes
        community_map = {node: -1 for node in self.graph.nodes()}
        for i, community in enumerate(self.communities):
            for node in community:
                community_map[node] = i

        # Separate clustered and unclustered nodes
        clustered_nodes = [node for node in self.graph.nodes() if community_map[node] != -1]
        unclustered_nodes = [node for node in self.graph.nodes() if community_map[node] == -1]

        plt.figure(figsize=(10, 10))

        # Draw unclustered nodes in black
        if unclustered_nodes:
            nx.draw_networkx_nodes(
                self.graph,
                pos,
                nodelist=unclustered_nodes,
                node_color='black',
                node_size=100,
                edgecolors='white'  # white edge for better visibility
            )

        # Draw clustered nodes
        if clustered_nodes:
            nx.draw_networkx_nodes(
                self.graph,
                pos,
                nodelist=clustered_nodes,
                node_color=[community_map[node] for node in clustered_nodes],
                cmap=plt.cm.rainbow,
                node_size=100,
                edgecolors='black'
            )

        nx.draw_networkx_edges(self.graph, pos, alpha=0.3)

        unclustered_count = len(unclustered_nodes)
        title = f'{self.__class__.__name__} Communities (n={len(self.communities)})'
        if unclustered_count > 0:
            title += f'\nUnclustered nodes: {unclustered_count}'
        plt.title(title)

        plt.axis('off')
        plt.show()

    def calculate_modularity(self):
        """
        Calculate modularity score for detected communities.
        :return: Float value representing modularity of the network partition
        :raises ValueError: If communities haven't been detected yet
        """
        if self.communities is None:
            raise ValueError("Run the algorithm first using run() method")
        return nx.community.modularity(self.graph, self.communities)

    def print_communities(self):
        """
        Print detected communities in human-readable format.
        :return: None
        :raises ValueError: If communities haven't been detected yet
        """
        if self.communities is None:
            raise ValueError("Run the algorithm first using run() method")
        logger.info(f"Found {len(self.communities)} communities:")
        for i, community in enumerate(self.communities, 1):
            logger.info(f"Community {i}: {sorted(community)}")


class GirvanNewmanAlgo(CommunityDetectionAlgorithm):
    def run(self, n):
        """Run Girvan-Newman algorithm for n divisions"""
        num_nodes = len(self.graph)
        self.labels = np.zeros((n, num_nodes))
        G = self.graph.copy()

        for division in range(n):
            self._remove_bridges(G)
            self.communities = list(nx.connected_components(G))
            for i, cc in enumerate(self.communities):
                indices = [self.node_to_index[node] for node in cc]
                self.labels[division, indices] = i

        return self.labels

    def _remove_bridges(self, G):
        """Helper method to remove bridges"""
        connected_components_start = len(list(nx.connected_components(G)))
        while len(list(nx.connected_components(G))) == connected_components_start:
            edge_betweenness = nx.edge_betweenness_centrality(G)
            max_edge = max(edge_betweenness.items(), key=lambda x: x[1])[0]
            G.remove_edge(max_edge[0], max_edge[1])


class KCliquePercolation(CommunityDetectionAlgorithm):
    def run(self, k):
        """Run K-Clique Percolation algorithm"""
        self.k = k
        self.communities = list(nx.community.k_clique_communities(self.graph, k))
        return self.communities


class FastCommunityUnfolding(CommunityDetectionAlgorithm):
    def run(self, resolution=1.0, seed: int = 42):
        """Run Louvain community detection"""
        self.communities = nx.community.louvain_communities(self.graph, resolution=resolution, seed=seed)
        return self.communities


class Walktrap(CommunityDetectionAlgorithm):
    def run(self):
        """Run Walktrap community detection"""
        walktrap_communities = algorithms.walktrap(self.graph)
        self.communities = walktrap_communities.communities
        return self.communities


def get_clique_size_distribution(
        graph: nx.Graph, filename: Union[Path, str] = FIGURES_DIR / 'table_clique_size_distribution.md'
) -> pd.DataFrame:
    """
    Calculate the number of cliques for each clique size in the graph and optionally save as markdown table.
    :param graph: NetworkX graph to analyze
    :param filename: Path to save the markdown table output. Defaults to 'table_clique_size_distribution.md' in FIGURES_DIR
    :return: dictionary mapping clique sizes to their frequency counts in the graph
    """
    all_cliques = list(nx.find_cliques(graph))
    size_distribution = Counter(len(clique) for clique in all_cliques)
    sorted_distribution = dict(sorted(size_distribution.items(), reverse=True))
    df = pd.DataFrame(
        [(size, count) for size, count in sorted_distribution.items()],
        columns=['Size', 'Count']
    )

    # Save to markdown using the provided function
    save_table_to_markdown(
        df=df,
        filename=filename,
        table_title="Clique Size Distribution"
    )

    return df


def find_top_n_cliques(graph: nx.Graph, n: int = 5):
    """
    Find the largest maximal cliques in the graph and print their details.
    :param graph: NetworkX graph to analyze
    :param n: Number of largest cliques to find and display
    :return: list of cliques, where each clique is a list of node IDs
    """
    all_cliques = list(nx.find_cliques(graph))
    top_sorted_cliques = sorted(all_cliques, key=len, reverse=True)[:n]

    # Print results
    print(f"\nTop {n} cliques found:")
    for i, clique in enumerate(top_sorted_cliques, 1):
        print(f"\nClique {i}:")
        print(f"Size: {len(clique)}")
        print(f"Node IDs: {sorted(clique)}")


class LPACommunityDetection(CommunityDetectionAlgorithm):
    """
    Implementation of Label Propagation Algorithm (LPA) for community detection
    using NetworkX's asynchronous label propagation method.
    :param graph: NetworkX graph object to analyze
    :param seed: Random seed for reproducibility (optional)
    :param weight: Edge attribute that contains the edge weight (optional)
    :param max_iter: Maximum number of iterations (default: 1000)
    """

    def __init__(self, graph: nx.Graph, weight: str = None, seed: int = 42, max_iter: int = 1000):
        """
        Initialize LPA community detection algorithm.
        :param graph: NetworkX graph object to analyze
        :param seed: Random seed for reproducibility
        :param weight: Edge attribute that contains the edge weight
        :param max_iter: Maximum number of iterations
        """
        super().__init__(graph)
        self.seed = seed
        self.weight = weight
        self.max_iter = max_iter

    def run(self):
        """
        Execute the Label Propagation Algorithm to detect communities.
        :return: self for method chaining
        :raises Exception: If algorithm execution fails
        """
        try:
            community_generator = nx.community.asyn_lpa_communities(
                self.graph,
                weight=self.weight,
                seed=self.seed,
            )

            self.communities = list(community_generator)

            logger.info(f"Successfully detected {len(self.communities)} communities using LPA")
            return self

        except Exception as e:
            logger.error(f"Error during LPA community detection: {str(e)}")
            raise

    def get_node_community_mapping(self):
        """
        Create a dictionary mapping nodes to their community index.
        :return: Dictionary with nodes as keys and community indices as values
        :raises ValueError: If communities haven't been detected yet
        """
        if self.communities is None:
            raise ValueError("Run the algorithm first using run() method")

        community_mapping = {}
        for idx, community in enumerate(self.communities):
            for node in community:
                community_mapping[node] = idx
        return community_mapping

    def get_community_sizes(self):
        """
        Get the sizes of all detected communities.
        :return: List of community sizes
        :raises ValueError: If communities haven't been detected yet
        """
        if self.communities is None:
            raise ValueError("Run the algorithm first using run() method")

        return [len(community) for community in self.communities]

    def get_largest_community(self):
        """
        Get the largest community by number of nodes.
        :return: Set of nodes in the largest community
        :raises ValueError: If communities haven't been detected yet
        """
        if self.communities is None:
            raise ValueError("Run the algorithm first using run() method")

        return max(self.communities, key=len)
