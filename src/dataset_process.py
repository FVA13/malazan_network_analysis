import yaml
import typer
import pickle
import pandas as pd
import networkx as nx
from loguru import logger
from pathlib import Path

from src.config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
    PARAMS,
)
from src import my_utils

app = typer.Typer()


@app.command()
def main(
        input_edges_path: Path = INTERIM_DATA_DIR / 'edges_data.csv',
        input_nodes_path: Path = INTERIM_DATA_DIR / 'nodes_data.csv',
        output_dir: Path = PROCESSED_DATA_DIR,
        params_path: Path = PARAMS,
):
    logger.info("Transforming edges and nodes data")

    with open(params_path, 'r') as f:
        params = yaml.safe_load(f)

    edges_data_processed = (
        pd.read_csv(input_edges_path)
        .query(
            "total_co_occurance > @params['min_co_occurence_threshold']"
        )  # filter out connections with few interactions over all books
        .reset_index(drop=True)
        .query("name1 not in ['Maybe', 'Hood'] and name2 not in ['Maybe', 'Hood']")
        # .rename(columns={"name1": "Source", "name2": "Target"})
    )
    nodes_data = (
        pd.read_csv(input_nodes_path)
    )

    # Create nx.Graph object
    G = nx.from_pandas_edgelist(
        edges_data_processed,
        source='name1',
        target='name2',
        edge_attr='total_co_occurance',
    )

    # Create node attributes for the Graph
    for column in nodes_data.columns:
        if column != 'id':  # Skip the name column since it's the node identifier
            attr_dict = nodes_data.set_index('id')[column].to_dict()
            nx.set_node_attributes(G, attr_dict, column)

    # Remove self-loops if there are any
    G.remove_edges_from(nx.selfloop_edges(G))

    largest_cc = max(nx.connected_components(G), key=lambda cc: len(cc))
    largest_cc_subgraph = G.subgraph(largest_cc)

    nodes_data_processed = (
        nodes_data
        .merge(
            my_utils.centralities(G).reset_index(),
            how='left',
            left_on='id',
            right_on='index'
        )
        .merge(
            pd.Series(nx.pagerank(G), name='pagerank').reset_index(),
            how='left',
            left_on='id',
            right_on='index'
        )
        .drop(columns=['index_x', 'index_y'])
        .assign(core_number=lambda df: df['id'].map(nx.core_number(G)).fillna(0))
        .assign(k_clique_percolation=lambda df: df['id'].map(
            {node: i for i, comm in
             enumerate(nx.community.k_clique_communities(largest_cc_subgraph, params['k_clique_percolation_base'])) for
             node in comm}
            ).fillna(-1)
        )
        .assign(louvain_community=lambda df: df['id'].map(
            {node: i for i, comm in enumerate(
                nx.community.louvain_communities(largest_cc_subgraph,
                                                 resolution=params['louvain_communities_resolution'])
                ) for node in comm}
            ).fillna(-1)
        )
        .assign(asyn_lpa_community=lambda df: df['id'].map(
            {node: i for i, comm in enumerate(
                nx.community.asyn_lpa_communities(
                    largest_cc_subgraph,
                    weight='total_co_occurance'
                    )
                ) for node in comm}
            ).fillna(-1)
        )
        .astype({"core_number": "int", "k_clique_percolation": "int", "louvain_community": "int"})
        # .rename(columns={"id": "Id", "norm_name": "Label"})
    )

    with open(output_dir / "graph.pkl", "wb") as f:
        pickle.dump(G, f)
    nodes_data_processed.to_csv(output_dir / "nodes_data_processed.csv", index=False)
    edges_data_processed.to_csv(output_dir / "edges_data_processed.csv", index=False)

    logger.success("Data transformed and saved")


if __name__ == '__main__':
    app()
