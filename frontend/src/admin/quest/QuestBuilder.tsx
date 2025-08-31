import React, { useState, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  Background,
  Controls,
} from 'reactflow';
import 'reactflow/dist/style.css';

export interface QuestBuilderProps {
  initial?: { nodes: Node[]; edges: Edge[] };
  onChange?: (graph: { nodes: Node[]; edges: Edge[] }) => void;
}

/**
 * QuestBuilder provides a simple graph editor for quest stages and branches.
 * Nodes represent stages and edges represent choices leading to the next stage.
 */
const QuestBuilder: React.FC<QuestBuilderProps> = ({ initial, onChange }) => {
  const [nodes, setNodes] = useState<Node[]>(initial?.nodes || []);
  const [edges, setEdges] = useState<Edge[]>(initial?.edges || []);

  const notify = useCallback(
    (n: Node[], e: Edge[]) => {
      onChange?.({ nodes: n, edges: e });
    },
    [onChange]
  );

  const onConnect = useCallback(
    (params: Edge | Connection) => {
      const edge: Edge = {
        ...(params as Connection),
        id: `${params.source}-${params.target}`,
      };
      setEdges((eds) => {
        const next = addEdge(edge, eds);
        notify(nodes, next);
        return next;
      });
    },
    [nodes, notify]
  );

  const addStage = useCallback(() => {
    const id = `stage_${nodes.length + 1}`;
    const newNode: Node = {
      id,
      data: { label: id },
      position: { x: Math.random() * 200, y: Math.random() * 200 },
    };
    setNodes((nds) => {
      const next = nds.concat(newNode);
      notify(next, edges);
      return next;
    });
  }, [nodes, edges, notify]);

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      const label = prompt('Branch label', edge.label as string) || '';
      setEdges((eds) => {
        const next = eds.map((e) =>
          e.id === edge.id ? { ...e, label } : e
        );
        notify(nodes, next);
        return next;
      });
    },
    [nodes, notify]
  );

  return (
    <div style={{ height: 500 }}>
      <button onClick={addStage}>Add Stage</button>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onConnect={onConnect}
        onEdgeClick={onEdgeClick}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default QuestBuilder;
