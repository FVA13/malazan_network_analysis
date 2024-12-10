# to suppress plots
import matplotlib; matplotlib.use('Agg')

import yaml
import typer
import pickle
import pandas as pd
from loguru import logger
from pathlib import Path

from src.config import (
    FIGURES_DIR,
    PROCESSED_DATA_DIR,
    PARAMS,
)
from src import (
    my_utils,
    community_detection,
    structural_analysis,
)

app = typer.Typer()


@app.command()
def main(
        input_path_graph: Path = PROCESSED_DATA_DIR / "graph.pkl",
        input_path_nodes: Path = PROCESSED_DATA_DIR / "nodes_data_processed.csv",
        figures_dir: Path = FIGURES_DIR,
        params: Path = PARAMS,
):
    logger.info("Generating plot from data...")

    with open(input_path_graph, "rb") as f:
        G = pickle.load(f)

    with open(params, 'r') as f:
        params = yaml.safe_load(f)

    nodes_data = pd.read_csv(input_path_nodes)


    # Graph Overview
    logger.info("Graph Overview")
    my_utils.get_graph_overview(G)
    my_utils.plot_power_degree_histogram(G)
    my_utils.plot_power_degree_distribution(G)
    analysis = my_utils.PowerLawAnalysis(G)
    analysis.plot_distribution(title='Malazan Network Degree Distribution')

    # Structure Analysis
    logger.info("Structural Analysis")
    structure_analyser = structural_analysis.NetworkStructuralAnalyser(G, ws_rewire_probe=params['ws_rewire_probe'])
    _ = structure_analyser.analyze_network_properties()
    structure_analyser.plot_attribute_mixing(G, 'gender')
    structure_analyser.plot_attribute_mixing(G, 'race_first')
    structure_analyser.plot_attribute_mixing(G, 'affiliation_first')
    structure_analyser.plot_attribute_mixing(G, 'affiliation_second')
    structure_analyser.plot_node_similarity_matrix(
        G,
        top_nodes=nodes_data.nlargest(20, 'degree')['id'].tolist(),
        similarity_metric='jaccard'
    )

    structural_analysis.get_centrality(nodes_data, column_name='total_words_count', centrality_name='pov')
    structural_analysis.get_centrality(nodes_data, column_name='degree', centrality_name='degree')
    structural_analysis.get_centrality(nodes_data, column_name='closeness', centrality_name='closeness')
    structural_analysis.get_centrality(nodes_data, column_name='betweenness', centrality_name='betweenness')
    structural_analysis.get_centrality(nodes_data, column_name='eigenvector', centrality_name='eigenvector')
    structural_analysis.get_centrality(nodes_data, column_name='pagerank', centrality_name='pagerank')
    structural_analysis.plot_centralities_pairplot(nodes_data)
    structural_analysis.plot_centralities_corr_matrix(nodes_data)
    structural_analysis.get_weights_between_top_nodes(nodes_data, G)

    # Community Detection
    logger.info("Community Detection")
    community_detection.get_clique_size_distribution(G)
    community_detection.find_top_n_cliques(G, 3)

    logger.success("Plot generation complete.")


if __name__ == "__main__":
    app()
