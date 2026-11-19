"""Launch the local web application or rebuild the API knowledge graph."""

from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parent
    sys.path[:0] = [str(root / "1_HITL"), str(root / "2_Coder")]
    if sys.argv[1:2] == ["build-graph"]:
        from knowledge_graph.build import main as build_graph

        del sys.argv[1]
        build_graph()
    else:
        from web.app import main as start_web

        start_web()


if __name__ == "__main__":
    main()
