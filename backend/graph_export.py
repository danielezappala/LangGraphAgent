# Utility per esportare il grafo agentico in vari formati (Mermaid, DOT, PNG, SVG)

def export_graph(graph, out_dir="."):
    """
    Esporta il grafo agentico LangGraph in vari formati (Mermaid, DOT, PNG, SVG) nella directory specificata.
    Richiede pygraphviz per PNG/SVG.
    """
    import os
    os.makedirs(out_dir, exist_ok=True)
    g = graph.get_graph()
    # 1. Mermaid
    try:
        mermaid_str = g.draw_mermaid()
        with open(os.path.join(out_dir, "graph_agent_mermaid.mmd"), "w") as f:
            f.write(mermaid_str)
        print(f"[EXPORT] Grafo Mermaid salvato in {out_dir}/graph_agent_mermaid.mmd")
    except Exception as e:
        print(f"[WARN] Impossibile esportare Mermaid: {e}")
    # 2. DOT
    try:
        dot_str = g.draw_dot()
        with open(os.path.join(out_dir, "graph_agent.dot"), "w") as f:
            f.write(dot_str)
        print(f"[EXPORT] Grafo DOT salvato in {out_dir}/graph_agent.dot")
    except Exception as e:
        print(f"[WARN] Impossibile esportare DOT: {e}")
    # 3. PNG/SVG (pygraphviz)
    try:
        png_path = os.path.join(out_dir, "graph_agent.png")
        svg_path = os.path.join(out_dir, "graph_agent.svg")
        g.draw_png(png_path)
        print(f"[EXPORT] Grafo PNG salvato in {png_path}")
        g.draw_svg(svg_path)
        print(f"[EXPORT] Grafo SVG salvato in {svg_path}")
    except Exception as e:
        print(f"[WARN] Impossibile esportare PNG/SVG: {e}\nInstalla pygraphviz se vuoi questi formati.")

if __name__ == "__main__":
    from basic_chatbot import graph
    export_graph(graph, out_dir=".")
