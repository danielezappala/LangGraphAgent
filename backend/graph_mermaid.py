# Utility per esportare un grafo LangGraph (CompiledStateGraph) in sintassi Mermaid

def stategraph_to_mermaid(graph):
    """
    Converte un grafo LangGraph compilato in una stringa Mermaid (graph TD ...)
    Usa solo API pubbliche di CompiledStateGraph (nodes, get_graph) per robustezza.
    """
    try:
        # 1. nodes property
        nodes = getattr(graph, "nodes", None)
        # 2. get_graph (networkx)
        g = graph.get_graph() if hasattr(graph, "get_graph") else None
        edges = []
        if g is not None:
            nodes = list(g.nodes)
            edges = list(g.edges)
            print(f"[DEBUG] NODI estratti da get_graph(): {nodes}")
            print(f"[DEBUG] ARCHI estratti da get_graph(): {edges}")
            # Logga warning se end_node non è destinazione di alcun edge
            end_targets = [e[1] if isinstance(e, (tuple, list)) else getattr(e, 'target', None) for e in edges]
            if 'end_node' not in end_targets:
                print("[WARN] end_node non è destinazione di alcun edge!")
            # Logga nodi orfani
            orphan_nodes = set(nodes) - set([e[0] for e in edges]) - set([e[1] for e in edges])
            if orphan_nodes:
                print(f"[WARN] Nodi orfani (nessun edge in ingresso/uscita): {orphan_nodes}")
        elif nodes is not None:
            nodes = list(nodes)
            # Nessun edge noto
            edges = []
        else:
            return 'graph TD\nA[Start] --> B[End]'
        # Mappa nomi tecnici a user-friendly solo per la visualizzazione
        label_map = {
            'start_node': 'Start',
            'intent_extraction': 'Intent Extraction',
            'weather_tool': 'Weather Tool',
            'llm_response': 'LLM Response',
            'llm_node': 'LLM',
            'end_node': 'End',
        }
        if not edges:
            # Mostra comunque tutti i nodi come orfani per debug visuale
            lines = ['graph TD']
            for n in nodes:
                label = label_map.get(n, n).replace(' ', '_')
                lines.append(f'{label}[{label}]')
            lines.append('A[Errore] --> B[Nessun edge trovato nel grafo]')
            mermaid_str = '\n'.join(lines)
            print(f"[MERMAID DEBUG]\n{mermaid_str}")
            return mermaid_str
        else:
            lines = ['graph TD']
            # Prima: dichiara tutti i nodi come nodi orfani (evita duplicati)
            already_declared = set()
            for n in nodes:
                if n in ('__start__', '__end__'):
                    continue  # Non mostrare nodi tecnici
                node_id = label_map.get(n, n).replace(' ', '_')
                node_label = label_map.get(n, n)
                if node_id not in already_declared:
                    lines.append(f'{node_id}[{node_label}]')
                    already_declared.add(node_id)
            # Edges
            edge_set = set()
            for edge in edges:
                if hasattr(edge, "source") and hasattr(edge, "target"):
                    src, dst = edge.source, edge.target
                elif isinstance(edge, (tuple, list)) and len(edge) >= 2:
                    src, dst = edge[0], edge[1]
                else:
                    continue
                if src in ('__start__', '__end__') or dst in ('__start__', '__end__'):
                    continue  # Non mostrare archi tecnici
                src_id = label_map.get(src, src).replace(' ', '_')
                dst_id = label_map.get(dst, dst).replace(' ', '_')
                edge_set.add((src_id, dst_id))
                lines.append(f'{src_id} --> {dst_id}')
            # Workaround: aggiungi archi condizionali noti se mancanti
            cond_edges = [("intent_extraction", "weather_tool"), ("intent_extraction", "llm_response")]
            for src, dst in cond_edges:
                src_id = label_map.get(src, src).replace(' ', '_')
                dst_id = label_map.get(dst, dst).replace(' ', '_')
                if (src in nodes and dst in nodes) and (src_id, dst_id) not in edge_set:
                    lines.append(f'{src_id} -.-> {dst_id}')  # tratteggiato per distinguere
            return '\n'.join(lines)


    except Exception as e:
        return f'graph TD\nA[Errore] --> B[{str(e)}]'
