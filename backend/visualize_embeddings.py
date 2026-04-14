"""
Visualize Skill Embeddings in 3D Space

Fetches skill vectors from Supabase, reduces to 3D with UMAP,
and opens an interactive Plotly scatter plot where similar skills
cluster together.

Usage:
    cd backend
    python visualize_embeddings.py

Install extras if needed:
    pip install umap-learn plotly pandas
"""

import asyncio
import sys
import logging
from pathlib import Path

import asyncpg
import numpy as np
import pandas as pd
import plotly.express as px
import umap

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "matching-service"))
from app.config import get_settings  # noqa: E402

settings = get_settings()

CATEGORY_COLORS = {
    "Programming Languages":    "#4C72B0",
    "Frontend Frameworks":      "#DD8452",
    "Backend Frameworks":       "#55A868",
    "Databases":                "#C44E52",
    "Cloud & DevOps":           "#8172B3",
    "AI & Machine Learning":    "#937860",
    "Methodologies":            "#DA8BC3",
    "Interpersonal":            "#8C8C8C",
    "Cognitive":                "#CCB974",
    "Management":               "#64B5CD",
    "Data Analysis":            "#E377C2",
    "Data Visualization":       "#7F7F7F",
    "Version Control":          "#BCBD22",
    "Project Management Tools": "#17BECF",
}


async def fetch_vectors(conn: asyncpg.Connection) -> pd.DataFrame:
    rows = await conn.fetch(
        """
        SELECT
            se.canonical_name,
            st.category,
            st.parent_category,
            se.embedding::text AS embedding_text
        FROM skill_embeddings se
        JOIN skill_taxonomy st ON st.id = se.skill_id
        WHERE se.embedding IS NOT NULL;
        """
    )

    if not rows:
        raise RuntimeError("No skill embeddings found — run setup_vector_db.py first")

    records = []
    for r in rows:
        vec = list(map(float, r["embedding_text"].strip("[]").split(",")))
        records.append({
            "name":            r["canonical_name"],
            "category":        r["category"] or "Other",
            "parent_category": r["parent_category"] or "Other",
            "vector":          vec,
        })

    logger.info(f"Fetched {len(records)} skill vectors")
    return pd.DataFrame(records)


def reduce_to_3d(df: pd.DataFrame) -> pd.DataFrame:
    matrix = np.array(df["vector"].tolist())
    n_skills = len(df)
    n_neighbors = min(5, n_skills - 1)

    logger.info(f"Running UMAP on {n_skills} skills (n_neighbors={n_neighbors})...")
    reducer = umap.UMAP(
        n_components=3,
        n_neighbors=n_neighbors,
        min_dist=0.1,
        metric="cosine",
        random_state=42,
    )
    coords = reducer.fit_transform(matrix)

    df["x"] = coords[:, 0]
    df["y"] = coords[:, 1]
    df["z"] = coords[:, 2]
    return df


def plot_3d(df: pd.DataFrame):
    fig = px.scatter_3d(
        df,
        x="x", y="y", z="z",
        color="category",
        text="name",
        hover_name="name",
        hover_data={
            "category": True,
            "parent_category": True,
            "x": False, "y": False, "z": False,
        },
        title="TalentIntel — Skill Embedding Clusters (3D)",
        color_discrete_map=CATEGORY_COLORS,
        height=850,
    )

    fig.update_traces(
        marker=dict(
            size=8,
            opacity=0.9,
            line=dict(width=1, color="white")
        ),
        textposition="top center",
        textfont=dict(size=12, color="white", family="Arial Black"),
        texttemplate="%{text}",
        hovertemplate="<b>%{hover_name}</b><br>Category: %{customdata[0]}<br>Parent Category: %{customdata[1]}<extra></extra>",
    )

    fig.update_layout(
        scene=dict(
            xaxis_title="UMAP-1",
            yaxis_title="UMAP-2",
            zaxis_title="UMAP-3",
            bgcolor="black",
            xaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.2)",
                title_font=dict(color="white"),
                tickfont=dict(color="white"),
                backgroundcolor="black"
            ),
            yaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.2)",
                title_font=dict(color="white"),
                tickfont=dict(color="white"),
                backgroundcolor="black"
            ),
            zaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.2)",
                title_font=dict(color="white"),
                tickfont=dict(color="white"),
                backgroundcolor="black"
            ),
        ),
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white",
        legend_title_text="Category",
        legend=dict(
            font=dict(color="white"),
            bgcolor="black",
            bordercolor="rgba(255, 255, 255, 0.2)"
        ),
        title=dict(
            font=dict(color="white", size=20),
            x=0.5
        ),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    out_path = ROOT / "skill_clusters_3d.html"
    fig.write_html(str(out_path))
    logger.info(f"Saved interactive chart → {out_path}")
    fig.show()


async def main():
    conn = await asyncpg.connect(settings.database_url, ssl="require")
    try:
        df = await fetch_vectors(conn)
    finally:
        await conn.close()

    df = reduce_to_3d(df)
    plot_3d(df)


if __name__ == "__main__":
    asyncio.run(main())
