import yaml
import numpy as np
import pandas as pd
import networkx as nx
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import combinations
from typing import (
    Dict,
    List,
    Union,
)
from pathlib import Path
from loguru import logger

from src.config import (
    REPORTS_DIR,
    FIGURES_DIR,
)


def update_yaml(new_data: dict[str, float], yaml_path: Union[Path, str] = REPORTS_DIR / 'results.yaml'):
    """
    Update or create a YAML file with new data, converting numpy values to native Python types.
    :param new_data: dictionary containing keys and values to update/add in the YAML file
    :param yaml_path: path to the YAML file (defaults to 'results.yaml' in REPORTS_DIR)
    :return: None
    """
    # Convert numpy values to native Python types
    cleaned_data = {}
    for key, value in new_data.items():
        if isinstance(value, np.generic):  # if value is a numpy type
            cleaned_data[key] = value.item()  # convert to native Python type
        else:
            cleaned_data[key] = value

    # Read existing data if file exists
    if Path(yaml_path).exists():
        with open(yaml_path, 'r') as f:
            existing_data = yaml.safe_load(f) or {}
    else:
        existing_data = {}

    # Update existing data with new values
    existing_data.update(cleaned_data)

    # Write back to file
    with open(yaml_path, 'w') as f:
        yaml.dump(existing_data, f, sort_keys=False)


def save_table_to_markdown(df: pd.DataFrame, filename: Union[Path, str], table_title=None):
    """
    Transform pandas DataFrame into markdown format and write to specified file with optional title.
    :param df: pandas DataFrame to be converted to markdown
    :param filename: destination file path for the markdown table
    :param table_title: optional header text to be added above table
    :return: None, writes markdown formatted table to file
    """
    # Verify input is a DataFrame
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    # Convert DataFrame to markdown
    markdown_table = df.to_markdown(index=False)

    # Prepare the content with optional title
    content = f"## {table_title}\n\n" if table_title else ""
    content += markdown_table + "\n\n"

    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    # logger.info(f"Table successfully saved to {filename}")


def get_graph_overview(
        graph: nx.Graph, save_to_yaml: bool = True, print_plots: bool = True
) -> Dict[str, Union[float, int, List]]:
    """
    This function calculates the overview graph metrics and prints them
    :param graph: NetworkX graph object to analyze
    :param save_to_yaml: Whether to save statistics to yaml file
    :param print_plots: True if plots should be printed
    :return: dictionary with statistics
    """
    largest_cc = max(nx.connected_components(graph), key=lambda cc: len(cc))
    largest_cc_subgraph = graph.subgraph(largest_cc)

    results = {
        'connected_components_number': len(list(nx.connected_components(graph))),
        'network_radius': nx.radius(largest_cc_subgraph), 'network_diameter': nx.diameter(largest_cc_subgraph),
        'avg_clustering': np.round(nx.average_clustering(graph), 3),
        'global_clustering': np.round(nx.transitivity(graph), 3),
        'avg_shortest_path_length': np.round(nx.average_shortest_path_length(largest_cc_subgraph), 3),
        'greatest_connected_component_size_ratio': np.round(len(largest_cc) / graph.number_of_nodes(), 3)
    }

    if save_to_yaml:
        update_yaml(results)

    print(f"Number of Connected Components within a Graph: {results['connected_components_number']}")
    print(f"Network Radius (largest CC): {results['network_radius']}")
    print(f"Network Diameter (largest CC): {results['network_diameter']}")
    print(f"Avg. Clustering: {results['avg_clustering']}")
    print(f"Avg. Shortest Path Length (largest CC): {results['avg_shortest_path_length']}")

    if print_plots:
        plot_clustering_coefficient_histogram(graph)
        plot_shortest_paths_distribution(graph)

    return results


def plot_clustering_coefficient_histogram(
        graph: nx.Graph, filename: Union[Path, str] = FIGURES_DIR / 'clustering_histogram.png'
):
    """
    Create and save a histogram visualization of local clustering coefficients for nodes in the graph.
    :param graph: NetworkX graph object to analyze
    :param filename: Path where the generated histogram figure should be saved
    :return: None, saves figure to specified path and displays plot
    """

    local_cc_dict = nx.clustering(graph)
    cc_values = list(local_cc_dict.values())

    plt.figure(figsize=(10, 6))
    plt.hist(cc_values, bins=20, edgecolor='black')
    plt.xlabel('Local Clustering Coefficient')
    plt.ylabel('Frequency')
    plt.title('Histogram of Local Clustering Coefficients')
    plt.grid(True, alpha=0.3)

    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


def centralities(graph: nx.Graph) -> pd.DataFrame:
    """
    Calculate degree, closeness, betweenness, and eigenvector centralities of the graph.
    :return: mapping of centrality names to dictionaries of node:centrality_value pairs
    """
    centrality_measures = {
        'degree': nx.degree_centrality(graph),
        'closeness': nx.closeness_centrality(graph),
        'betweenness': nx.betweenness_centrality(graph),
        'eigenvector': nx.eigenvector_centrality(graph),
    }

    return pd.DataFrame({
        measure: pd.Series(values)
        for measure, values in centrality_measures.items()
    })


def empirical_cdf(graph: nx.Graph) -> np.array:
    """
    Calculate the empirical cumulative distribution function (eCDF) of node degrees in the graph.
    :param graph: NetworkX graph object
    :return: numpy array containing the cumulative probabilities for each degree value
    """
    degrees_frequency = nx.degree_histogram(graph)
    degrees_distribution = [el / sum(degrees_frequency) for el in degrees_frequency]
    # get eCDF
    for i in range(1, len(degrees_distribution)):
        degrees_distribution[i] = degrees_distribution[i - 1] + degrees_distribution[i]

    return np.array(degrees_distribution)


def plot_power_degree_histogram(
        graph: nx.Graph,
        filename: Union[Path, str] = FIGURES_DIR / 'power_degree_histogram.png'
):
    """
    Plot histogram of node degrees in the graph, limited to degrees up to 40.
    :param graph: NetworkX graph object to analyze
    :param filename: path where the plot will be saved
    :return: None
    """
    sns.histplot(nx.degree_histogram(graph))
    plt.xlabel('degree')
    plt.ylabel('probability')
    plt.title('Power Degree Histogram (limited by 40)')
    plt.xlim(left=0, right=40)

    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


def plot_power_degree_distribution(
        graph: nx.Graph, filename: Union[Path, str] = FIGURES_DIR / 'power_degree_ecdf.png'
):
    """
    Plot the empirical cumulative distribution function (ECDF) of node degrees in the graph.
    :param graph: NetworkX graph object to analyze
    :param filename: Path or string specifying where to save the plot (default: 'figures/power_degree_ecdf.png')
    :return: None
    """
    ecdf = empirical_cdf(graph)
    sns.lineplot(ecdf)
    plt.xlabel('degree')
    plt.ylabel('probability')
    plt.title('Power Degree Empirical CDF')

    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


def plot_shortest_paths_distribution(
        graph, filename: Union[Path, str] = FIGURES_DIR / 'shortest_paths_histogram.png'
):
    """
    Plot and save the distribution of shortest paths in the graph.
    :param graph: NetworkX graph object containing the network to analyze
    :param filename: Path or string specifying where to save the plot (default: 'figures/shortest_paths_histogram.png')
    :return: None
    """
    shortest_paths_lengths = []
    node_pairs = list(combinations(graph.nodes(), 2))

    # Calculate shortest paths for all pairs
    for source, target in node_pairs:
        try:
            # Get the shortest path as a list of nodes
            path = nx.shortest_path(graph, source, target, weight='weight')
            # Calculate the path length (number of edges)
            path_length = len(path) - 1
            shortest_paths_lengths.append(path_length)
        except nx.NetworkXNoPath:
            continue

    plt.figure(figsize=(10, 6))
    plt.hist(shortest_paths_lengths, bins='auto', edgecolor='black')
    plt.title('Distribution of Shortest Paths Lengths\n(Number of edges in path)', fontsize=14)
    plt.xlabel('Path Length (edges)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(True, alpha=0.3)

    # Add some statistics as text
    mean_path = np.mean(shortest_paths_lengths)
    median_path = np.median(shortest_paths_lengths)
    stats_text = f'Mean: {mean_path:.2f}\nMedian: {median_path:.2f}'
    plt.text(0.95, 0.95, stats_text,
             transform=plt.gca().transAxes,
             verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


class PowerLawAnalysis:
    """
    Analyzes and visualizes the power law characteristics of a graph's degree distribution.

    :param graph: NetworkX graph object to analyze
    :param filename: Path to save the generated plot (default: 'degree_distribution.png' in FIGURES_DIR)

    Methods:
        power_law_cdf(x, alpha, x_min): Calculates the cumulative distribution function for power law
        power_law_pdf(x, alpha, x_min): Calculates the probability density function for power law
        mle_power_law_params(): Estimates power law parameters using maximum likelihood estimation
        plot_distribution(title): Plots the degree distribution with fitted power law curve

    Attributes:
        graph: Input NetworkX graph
        degree_sequence: Array of node degrees from the graph
        filename: Path for saving the plot
    """

    def __init__(self, graph, filename: Union[Path, str] = FIGURES_DIR / 'degree_distribution.png'):
        self.graph = graph
        self.degree_sequence = np.array([graph.degree(node) for node in graph.nodes()])
        self.filename = filename

    @staticmethod
    def power_law_cdf(x, alpha=3.5, x_min=1):
        return 1 - (x_min / x) ** (alpha - 1)

    @staticmethod
    def power_law_pdf(x, alpha, x_min):
        return (alpha - 1) / x_min * (x / x_min) ** -alpha

    def mle_power_law_params(self):
        alpha_best, x_min_best, ks_value_best = float("-inf"), float("-inf"), float("inf")

        for x_min in range(int(self.degree_sequence.min()), int(self.degree_sequence.max())):
            filtered_sequence = self.degree_sequence[self.degree_sequence >= x_min]
            alpha = 1 + len(filtered_sequence) * (np.sum(np.log(filtered_sequence / x_min))) ** -1
            ks_value = stats.kstest(filtered_sequence, self.power_law_cdf, args=(alpha, x_min)).statistic

            if ks_value < ks_value_best:
                alpha_best, x_min_best, ks_value_best = alpha, x_min, ks_value

        return (alpha_best, x_min_best)

    def plot_distribution(self, title: str):
        hist, bin_edges = np.histogram(self.degree_sequence, bins=1000, density=True)
        bin_centers = (bin_edges[1:] + bin_edges[:-1]) / 2

        plt.figure(figsize=(10, 6))
        plt.scatter(bin_centers[hist > 0], hist[hist > 0], s=5)
        plt.title(title)

        hat_alpha, hat_x_min = self.mle_power_law_params()
        x_space = np.linspace(hat_x_min, self.degree_sequence.max(), 100)
        plt.plot(
            x_space,
            self.power_law_pdf(x_space, hat_alpha, hat_x_min),
            label=f'Power law α={hat_alpha:.2f}; x_min={hat_x_min:.2f}',
            c='tab:orange',
        )

        plt.xscale('log')
        plt.yscale('log')
        plt.ylim(0.001, 0.5)
        plt.legend()
        plt.grid(True)
        plt.savefig(self.filename, dpi=300, bbox_inches='tight')
        plt.show()
