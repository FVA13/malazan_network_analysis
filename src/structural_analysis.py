import numpy as np
import pandas as pd
import networkx as nx
from scipy import stats

import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

from typing import (
    Dict,
    List,
    Tuple,
    Literal,
)
from pathlib import Path
from loguru import logger

from src.config import (
    REPORTS_DIR,
    FIGURES_DIR,
)
from src.my_utils import (
    PowerLawAnalysis,
    save_table_to_markdown,
)


class NetworkStructuralAnalyser:
    """
    A class for analyzing and comparing network structural properties with random graph models.

    This class provides functionality to:
    - Generate different types of random networks (ER, BA, WS)
    - Analyze network properties including degree distribution, clustering, and path length
    - Compare empirical networks with random network models
    - Visualize network properties and comparisons

    Attributes:
        models (dict): Dictionary of network generation functions
        seed (int): Random seed for reproducibility
        ws_rewire_probe (float): Rewiring probability for Watts-Strogatz model

    Methods:
        generate_er: Generate Erdős-Rényi random graph
        generate_ba: Generate Barabási-Albert scale-free network
        generate_ws: Generate Watts-Strogatz small-world network
        analyze_degree_distribution: Analyze degree distribution properties
        analyze_clustering: Analyze clustering coefficient properties
        analyze_path_length: Analyze path length properties
        analyze_network_properties: Comprehensive network analysis
    """

    def __init__(self, graph: nx.Graph, ws_rewire_probe: float = 0.1):
        self.graph = graph
        self.models = {
            'ER': self.generate_er,
            'BA': self.generate_ba,
            'WS': self.generate_ws
        }
        self.seed = 42
        self.ws_rewire_probe = ws_rewire_probe

    @staticmethod
    def generate_er(n: int, avg_degree: float, seed: int = 42) -> nx.Graph:
        """Returns Erdos-Renyi graph based on number of nodes and average degree."""
        p = avg_degree / (n - 1)
        return nx.erdos_renyi_graph(n, p, seed=seed)

    @staticmethod
    def generate_ba(n: int, avg_degree: float, seed: int = 42) -> nx.Graph:
        """
        Returns Barabási–Albert preferential attachment graph based on number of nodes and average degree.
        :param n: Number of nodes in the network
        :param avg_degree: Desired average degree (number of connections) per node
        :param seed: Random seed for reproducibility (default: 42)
        :return: NetworkX graph object representing a Barabási-Albert network
        """
        m = max(1, int(avg_degree / 2))
        return nx.barabasi_albert_graph(n, m, seed=seed)

    @staticmethod
    def generate_ws(n: int, avg_degree: float, seed: int = 42, rewire_prob: float = 0.1) -> nx.Graph:
        """
        Returns Watts-Strogatz small-world graph based on number of nodes, average degree and rewiring probability.
        :param n: Number of nodes in the network
        :param avg_degree: Desired average degree (number of connections) per node, will be rounded to nearest even number
        :param seed: Random seed for reproducibility (default: 42)
        :param rewire_prob: Probability of rewiring each edge (between 0 and 1, default: 0.1)
        :return: NetworkX graph object representing a Watts-Strogatz small-world network
        """
        k = max(2, int(avg_degree))
        if k % 2 != 0:
            k += 1
        return nx.watts_strogatz_graph(n, k, seed=seed, p=rewire_prob)

    @staticmethod
    def analyze_degree_distribution(graph: nx.Graph) -> Dict[str, float]:
        """
        Analyze the degree distribution properties of a network.

        :param graph: NetworkX graph object to analyze
        :return: Dictionary containing alpha (power law exponent), x_min (minimum x value),
                degree_dist (degree distribution), and mean_degree
        """
        degrees = [d for n, d in graph.degree()]
        degree_counts = Counter(degrees)
        total_nodes = len(degrees)
        degree_dist = {k: v / total_nodes for k, v in degree_counts.items()}
        mean_degree = sum(degrees) / total_nodes

        # Estimate power law parameters
        power_law_analyzer = PowerLawAnalysis(graph)
        alpha, x_min = power_law_analyzer.mle_power_law_params()

        return {
            'alpha': alpha,
            'x_min': x_min,
            'degree_dist': degree_dist,
            'mean_degree': mean_degree,
        }

    @staticmethod
    def analyze_clustering(graph: nx.Graph) -> Dict[str, float]:
        """
        Calculate clustering coefficient metrics for the network.

        :param graph: NetworkX graph object to analyze
        :return: Dictionary containing average clustering coefficient, global clustering coefficient,
                and node-wise clustering distribution
        """
        return {
            'avg_clustering': nx.average_clustering(graph),
            'global_clustering': nx.transitivity(graph),
            'clustering_distribution': dict(nx.clustering(graph)),
        }

    @staticmethod
    def analyze_path_length(graph: nx.Graph) -> Dict[str, float]:
        """
        Analyze path length properties of the largest connected component.

        :param graph: NetworkX graph object to analyze
        :return: Dictionary containing average path length, diameter, and radius of the network
        """
        components = list(nx.connected_components(graph))
        if not components:
            logger.warning("No connected components in the graph!")
            return {
                'avg_path_length': None,
                'diameter': None,
                'radius': None,
                'component_size_ratio': 0
            }

        largest_cc = max(components, key=len)
        largest_subgraph = graph.subgraph(largest_cc)

        # Calculate component size ratio

        return {
            'avg_path_length': nx.average_shortest_path_length(largest_subgraph),
            'diameter': nx.diameter(largest_subgraph),
            'radius': nx.radius(largest_subgraph),
        }

    @staticmethod
    def plot_degree_distribution(graph: nx.Graph, label, ax=None):
        """
        Plot the degree distribution of a network in log-log scale.

        :param graph: NetworkX graph object to analyze
        :param label: Label for the plot legend
        :param ax: Matplotlib axes object to plot on (optional)
        :return: Matplotlib axes object with the plot
        """
        if ax is None:
            fig, ax = plt.subplots()

        degrees = [d for n, d in graph.degree()]
        degree_counts = Counter(degrees)
        total_nodes = len(degrees)
        x = sorted(degree_counts.keys())
        y = [degree_counts[k] / total_nodes for k in x]

        # Plot in log-log scale
        ax.loglog(x, y, 'o-', label=label, alpha=0.7, markersize=4)
        ax.set_xlabel('Degree (log)')
        ax.set_ylabel('Probability (log)')
        ax.grid(True, which="both", ls="-", alpha=0.2)
        return ax

    def _plot_comparisons(self, original_properties: Dict, model_graphs_properties: Dict):
        """
        Plot comprehensive comparisons between original and model networks.

        :param original_properties: Dictionary of original network properties
        :param model_graphs_properties: Dictionary of model networks properties
        :return: None
        """
        fig = plt.figure(figsize=(15, 12))

        # 1. Degree distribution
        ax1 = fig.add_subplot(221)
        self.plot_degree_distribution(original_properties['graph'], 'Original', ax1)
        for model_name, props in model_graphs_properties.items():
            self.plot_degree_distribution(props['graph'], model_name, ax1)
        ax1.legend()
        ax1.set_title('Degree Distribution')

        # 2. Clustering coefficient comparison
        ax2 = fig.add_subplot(222)
        clustering_values = {
            'Original': original_properties['clustering']['avg_clustering'],
            **{model: props['clustering']['avg_clustering']
               for model, props in model_graphs_properties.items()}
        }
        ax2.bar(clustering_values.keys(), clustering_values.values())
        ax2.set_title('Average Clustering Coefficient')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        # 3. Average path length comparison
        ax3 = fig.add_subplot(223)
        path_values = {
            'Original': original_properties['path_length']['avg_path_length'],
            **{model: props['path_length']['avg_path_length']
               for model, props in model_graphs_properties.items()}
        }
        # Filter out None values
        path_values = {k: v for k, v in path_values.items() if v is not None}
        if path_values:  # Only plot if there are valid values
            ax3.bar(path_values.keys(), path_values.values())
            ax3.set_title('Average Path Length')
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

        plt.savefig(FIGURES_DIR / 'random_networks_comparison.png', dpi=300, bbox_inches='tight')

    def _preprocess_network(graph: nx.Graph) -> nx.Graph:
        """Ensure network has consecutive integer node labels"""
        mapping = dict(zip(graph.nodes(), range(len(graph))))
        return nx.relabel_nodes(graph, mapping)

    @staticmethod
    def plot_summary(comparison: pd.DataFrame):
        """
        Create a comprehensive visual summary of all network comparison results.

        :param comparison: Pandas DataFrame containing comparison of network properties
        :return: None
        """
        fig = plt.figure(figsize=(15, 10))
        ax1 = fig.add_subplot(222)
        sns.heatmap(comparison.T, annot=True, cmap='YlOrRd', fmt='.3f', ax=ax1)
        ax1.set_title('Network Properties Comparison')
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'random_networks_summary.png', dpi=300, bbox_inches='tight')
        plt.show()

    def plot_random_networks(self):
        """
        Plot examples of different random network models using spring layout.

        :param n: Number of nodes in each network (default: 100)
        :param avg_degree: Average degree for the networks (default: 4)
        :return: None
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        n = self.graph.number_of_nodes()
        m = self.graph.number_of_edges()
        avg_degree = 2 * m / n

        # Generate and plot ER network
        G_er = self.generate_er(n, avg_degree)
        pos_er = nx.spring_layout(G_er)
        axes[0].set_title('Erdős-Rényi (ER)')
        nx.draw(G_er, pos_er, ax=axes[0],
                with_labels=False,
                edge_color='gray',
                node_size=40,
                alpha=0.5,
                edgecolors='black')

        # Generate and plot BA network
        G_ba = self.generate_ba(n, avg_degree)
        pos_ba = nx.spring_layout(G_ba)
        axes[1].set_title('Barabási-Albert (BA)')
        nx.draw(G_ba, pos_ba, ax=axes[1],
                with_labels=False,
                edge_color='gray',
                node_size=40,
                alpha=0.5,
                edgecolors='black')

        # Generate and plot WS network
        G_ws = self.generate_ws(n, avg_degree, rewire_prob=self.ws_rewire_probe)
        pos_ws = nx.spring_layout(G_ws)
        axes[2].set_title('Watts-Strogatz (WS)')
        nx.draw(G_ws, pos_ws, ax=axes[2],
                with_labels=False,
                edge_color='gray',
                node_size=40,
                alpha=0.5,
                edgecolors='black')

        plt.tight_layout()
        # plt.savefig(FIGURES_DIR / 'random_network_models.png', dpi=300, bbox_inches='tight')
        plt.show()

    @staticmethod
    def plot_attribute_mixing(
            graph: nx.Graph, attribute: str, figsize: Tuple[int, int] = (20, 20)
    ):
        """
        Calculate attribute assortativity and visualize mixing patterns through a heatmap.

        :param graph: NetworkX graph object
        :param attribute: Node attribute to analyze mixing patterns for
        :param figsize: Tuple specifying figure dimensions (width, height)
        :return: None. Displays and saves heatmap visualization

        The function:
        - Removes nodes with NaN values for the specified attribute
        - Creates a mixing matrix showing frequency of connections between attribute values
        - Calculates the assortativity coefficient
        - Plots a bottom triangle heatmap of the mixing matrix
        - Saves the plot directly to figures directory
        """
        # Create a subgraph without NaN nodes
        non_nan_nodes = [
            (n, d) for n, d in graph.nodes(data=True)
            if attribute in d and not (isinstance(d[attribute], float) and np.isnan(d[attribute]))
        ]

        G_clean = graph.subgraph([n for n, _ in non_nan_nodes])

        # Get unique attribute values
        attr_values = sorted(set(d[attribute] for _, d in non_nan_nodes))
        # Create mapping for attributes to indices
        attr_to_idx = {attr: idx for idx, attr in enumerate(attr_values)}
        # Calculate mixing matrix manually to ensure correct order
        n = len(attr_values)
        mixing_matrix = np.zeros((n, n))

        for u, v in G_clean.edges():
            u_attr = G_clean.nodes[u][attribute]
            v_attr = G_clean.nodes[v][attribute]
            i, j = attr_to_idx[u_attr], attr_to_idx[v_attr]
            mixing_matrix[i, j] += 1
            if i != j:  # Add to symmetric position if different attributes
                mixing_matrix[j, i] += 1

        # Calculate assortativity coefficient
        assort_coef = nx.attribute_assortativity_coefficient(G_clean, attribute)
        mask = np.triu(np.ones_like(mixing_matrix), k=1)
        plt.figure(figsize=figsize)

        # Format tick labels
        def format_tick_label(label):
            label_str = str(label)
            if len(label_str) > 20:
                return label_str[:17] + '...'
            return label_str

        formatted_labels = [format_tick_label(val) for val in attr_values]

        sns.heatmap(
            mixing_matrix,
            annot=True,
            fmt='.0f',
            cmap='Blues',
            xticklabels=formatted_labels,
            yticklabels=formatted_labels,
            cbar_kws={'label': 'Count'},
            mask=mask,
            square=True,
            annot_kws={'size': 20},
        )

        plt.xticks(rotation=45, ha='right', fontsize=20)
        plt.yticks(rotation=0, fontsize=20)
        # plt.title(f'Attribute Mixing Matrix\nAssortativity Coefficient: {assort_coef:.3f}')
        plt.xlabel(f'{attribute}', fontsize=20)
        plt.ylabel(f'{attribute}',fontsize=20)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / f'heatmap_assortativity_mixing_{attribute}.png', dpi=300, bbox_inches='tight')
        plt.show()

    @staticmethod
    def plot_node_similarity_matrix(
            graph: nx.Graph,
            top_nodes: List[str] = None,
            similarity_metric: Literal['jaccard', 'cosine'] = 'jaccard',
            figsize: Tuple[int, int] = (10, 8),
            cmap: str = 'Blues',
            show_labels: bool = True,
            weight_attr: str = None  # New parameter for weight attribute
    ):
        """
        Creates and plots a node similarity matrix for a given graph, showing how similar nodes are to each other based on their neighbors.
        Supports both weighted and unweighted graphs.

        :param graph: The input graph to analyze
        :type graph: nx.Graph
        :param top_nodes: List of node IDs to include in the visualization, if None all nodes are used
        :type top_nodes: List[str], optional
        :param similarity_metric: Method to calculate node similarity ('jaccard' or 'cosine')
        :type similarity_metric: Literal['jaccard', 'cosine']
        :param figsize: Width and height of the output plot in inches
        :type figsize: Tuple[int, int]
        :param cmap: Colormap name for the heatmap visualization
        :type cmap: str
        :param show_labels: Whether to display node labels on the plot axes
        :type show_labels: bool
        :param weight_attr: Name of the edge attribute containing weights (None for unweighted graphs)
        :type weight_attr: str, optional
        :return: Matrix containing pairwise similarity scores between nodes
        :rtype: numpy.ndarray
        """
        assert similarity_metric in ['jaccard', 'cosine'], "provided similarity_metric isn't implemented"

        # Initialize similarity matrix
        n_nodes = len(graph.nodes())
        similarity_matrix = np.zeros((n_nodes, n_nodes))
        nodes_list = list(graph.nodes())

        def get_neighbor_weights(node):
            """Helper function to get neighbors and their weights"""
            if weight_attr is None:
                # Unweighted case: return dict with all weights = 1
                return {neighbor: 1 for neighbor in graph.neighbors(node)}
            else:
                # Weighted case: return dict with actual weights
                return {neighbor: graph[node][neighbor][weight_attr] for neighbor in graph.neighbors(node)}

        # Calculate similarities
        for i, node1 in enumerate(nodes_list):
            for j, node2 in enumerate(nodes_list):
                neighbors1 = get_neighbor_weights(node1)
                neighbors2 = get_neighbor_weights(node2)

                if similarity_metric == 'jaccard':
                    neighbors1 = set(graph.neighbors(node1))
                    neighbors2 = set(graph.neighbors(node2))
                    if len(neighbors1.union(neighbors2)) == 0:
                        similarity = 0
                    else:
                        similarity = len(neighbors1.intersection(neighbors2)) / len(neighbors1.union(neighbors2))

                elif similarity_metric == 'cosine':
                    # For weighted cosine, use weights as vector components
                    if not neighbors1 or not neighbors2:
                        similarity = 0
                    else:
                        # Calculate dot product
                        dot_product = sum(
                            neighbors1.get(n, 0) * neighbors2.get(n, 0)
                            for n in set(neighbors1.keys()).intersection(set(neighbors2.keys()))
                        )
                        # Calculate magnitudes
                        mag1 = np.sqrt(sum(w * w for w in neighbors1.values()))
                        mag2 = np.sqrt(sum(w * w for w in neighbors2.values()))
                        similarity = dot_product / (mag1 * mag2) if mag1 * mag2 != 0 else 0

                similarity_matrix[i][j] = similarity

        # If top_nodes is specified, select those specific nodes
        if top_nodes is not None:
            # Verify all requested nodes exist in the graph
            if not all(node in nodes_list for node in top_nodes):
                raise ValueError("Some specified nodes do not exist in the graph")

            # Get indices of specified nodes
            top_indices = [nodes_list.index(node) for node in top_nodes]
            # Select submatrix of specified nodes
            similarity_matrix_display = similarity_matrix[top_indices][:, top_indices]
            nodes_display = top_nodes
        else:
            similarity_matrix_display = similarity_matrix
            nodes_display = nodes_list

        # Plot
        plt.figure(figsize=figsize)
        if show_labels:
            sns.heatmap(similarity_matrix_display, cmap=cmap,
                        xticklabels=nodes_display,
                        yticklabels=nodes_display)
        else:
            sns.heatmap(similarity_matrix_display, cmap=cmap)

        plt.title(f'Node Similarity Matrix (sim metric: {similarity_metric})')
        plt.tight_layout()
        plt.savefig(
            FIGURES_DIR / f'heatmap_nodes_structural_similarity_{similarity_metric}.png',
            dpi=300, bbox_inches='tight'
        )
        plt.show()

    def analyze_network_properties(self, plot=True):
        """
        Perform comprehensive network analysis and comparison with random models.

        :param graph: NetworkX graph object to analyze
        :param plot: Whether to generate visualization plots (default: True)
        :return: Pandas DataFrame containing comparison summary of network properties
        """
        # Load and preprocess network
        G_original = self.graph

        # Calculate basic properties
        n = G_original.number_of_nodes()
        m = G_original.number_of_edges()
        avg_degree = 2 * m / n

        # Analyze original network
        original_properties = {
            'graph': G_original,
            'degree_dist': self.analyze_degree_distribution(G_original),
            'clustering': self.analyze_clustering(G_original),
            'path_length': self.analyze_path_length(G_original)
        }

        # Generate and analyze random models
        model_graphs_properties = {}
        for model_name, generator in self.models.items():
            if model_name == 'WS':
                G_model = generator(n, avg_degree, seed=self.seed, rewire_prob=self.ws_rewire_probe)
            else:
                G_model = generator(n, avg_degree, seed=self.seed)
            model_graphs_properties[model_name] = {
                'graph': G_model,
                'degree_dist': self.analyze_degree_distribution(G_model),
                'clustering': self.analyze_clustering(G_model),
                'path_length': self.analyze_path_length(G_model)
            }

        # Create comparison summary
        comparison_data = {
            'Original': {
                'Avg Degree': original_properties['degree_dist']['mean_degree'],
                'Power Law α': original_properties['degree_dist']['alpha'],
                'Avg Clustering': original_properties['clustering']['avg_clustering'],
                'Avg Path Length': original_properties['path_length']['avg_path_length'],
                'KS statistic': None,
            }
        }

        for model_name, props in model_graphs_properties.items():
            # Calculate KS statistic between original model and generated random graph
            original_degrees = list(dict(G_original.degree()).values())
            model_degrees = list(dict(props['graph'].degree()).values())

            ks_stat, _ = stats.ks_2samp(
                original_degrees,
                model_degrees
            )

            comparison_data[model_name] = {
                'Avg Degree': props['degree_dist']['mean_degree'],
                'Power Law α': props['degree_dist']['alpha'],
                'Avg Clustering': props['clustering']['avg_clustering'],
                'Avg Path Length': props['path_length']['avg_path_length'],
                'KS statistic': ks_stat,
            }

        comparison_summary = pd.DataFrame(comparison_data)

        if plot:
            self._plot_comparisons(original_properties, model_graphs_properties)
            self.plot_summary(comparison_summary)
            # plt.savefig(FIGURES_DIR / 'network_analysis.png', dpi=300, bbox_inches='tight')

        return comparison_summary


def get_centrality(nodes_data: pd.DataFrame, column_name: str, centrality_name: str):
    data = (
        nodes_data
        .sort_values(by=column_name, ascending=False)
        .drop(columns=['norm_name', 'affiliation_second', 'pov_words_per_book_with_pov'])
        .reset_index(drop=True)
        .head(15)
    )
    mean_value = nodes_data[column_name].mean()
    percentile_90 = nodes_data[column_name].quantile(0.90)

    save_table_to_markdown(
        df=data,
        filename=FIGURES_DIR / f'table_top_{centrality_name}_centrality.md'
    )

    plt.figure(figsize=(10, 6))
    sns.barplot(data=data, x='id', y=column_name)
    plt.xticks(rotation=45)
    plt.axhline(y=mean_value, color='r', linestyle='--', label=f'Mean: {mean_value:.3f}')
    plt.axhline(y=percentile_90, color='g', linestyle='--', label=f'90th percentile: {percentile_90:.3f}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f'bar_plot_top_{centrality_name}_centrality.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_centralities_pairplot(nodes_data: pd.DataFrame, figures_dir: Path = FIGURES_DIR):
    sns.pairplot(nodes_data[['degree', 'closeness', 'betweenness', 'eigenvector', 'pagerank']])
    plt.savefig(figures_dir / f'pairplot_centralities_and_pagerank.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_centralities_corr_matrix(nodes_data: pd.DataFrame, figures_dir: Path = FIGURES_DIR):
    correlation_matrix = nodes_data[['degree', 'closeness', 'betweenness', 'eigenvector', 'pagerank']].corr()
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))

    # Create a heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix,
                mask=mask,
                annot=True,
                cmap='Blues',
                vmin=0,
                vmax=1,
                center=0.5,
                square=True)
    plt.title('Correlation Matrix of Network Metrics')
    plt.savefig(figures_dir / f'corr_centralities_and_pagerank.png', dpi=300, bbox_inches='tight')
    plt.show()


def get_weights_between_top_nodes(
        nodes_data: pd.DataFrame, graph: nx.Graph, figures_dir: Path = FIGURES_DIR
):
    top_nodes = nodes_data.nlargest(20, 'degree')['id'].tolist()
    # Get adjacency matrix for the whole graph and convert to dense numpy array
    adj_matrix = nx.adjacency_matrix(graph, weight='total_co_occurance')
    adj_matrix = adj_matrix.todense()
    # Convert to DataFrame with all node labels
    adj_df = pd.DataFrame(adj_matrix, index=list(graph.nodes()), columns=list(graph.nodes()))
    # Filter for top 100 nodes
    matrix = adj_df.loc[top_nodes, top_nodes]

    # Create heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        matrix,
        cmap='Blues',
        square=True,
        robust=True,
        mask=(matrix == 0)
    )  # Hide cells with zero values
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.title('Connection Weights between Top 20 Nodes by Degree')

    plt.tight_layout()
    plt.savefig(figures_dir / f'heatmap_edges_weights.png')
    plt.show()
