"use client";

import { useNodesState, useEdgesState, ReactFlow, Background, Controls, MarkerType, BackgroundVariant, Node, Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const nodeStyle = (accent: string) => ({
  background: "#0d0d0d",
  color: "#f0f0f0",
  border: `1px solid ${accent}`,
  borderRadius: "6px",
  padding: "10px 14px",
  fontSize: "11px",
  fontFamily: "var(--font-geist-mono)",
  minWidth: "150px",
  textAlign: "center" as const,
});

const initialNodes: Node[] = [
  // Compute Core cluster
  {
    id: "manager",
    position: { x: 300, y: 30 },
    data: { label: "Manager Node\nZMQ ROUTER :5555" },
    style: { ...nodeStyle("#ffffff"), fontWeight: "600", whiteSpace: "pre-line" },
  },
  {
    id: "policy",
    position: { x: 100, y: 160 },
    data: { label: "Policy Engine\npolicy.yaml validation" },
    style: { ...nodeStyle("#555555"), whiteSpace: "pre-line" },
  },
  {
    id: "ebpf",
    position: { x: 500, y: 160 },
    data: { label: "eBPF Shield\nforensic_snapshot.c" },
    style: { ...nodeStyle("#555555"), whiteSpace: "pre-line" },
  },
  {
    id: "athena",
    position: { x: 160, y: 310 },
    data: { label: "Athena Worker\nunshare sandbox" },
    style: { ...nodeStyle("#444444"), whiteSpace: "pre-line" },
  },
  {
    id: "lancedb",
    position: { x: 430, y: 310 },
    data: { label: "LanceDB\nVector Knowledge Store" },
    style: { ...nodeStyle("#444444"), whiteSpace: "pre-line" },
  },
  // Edge Node
  {
    id: "edge",
    position: { x: 300, y: 460 },
    data: { label: "Edge Gateway\nZMQ DEALER (Termux/ARM)" },
    style: { ...nodeStyle("#333333"), whiteSpace: "pre-line" },
  },
  {
    id: "sqlitevec",
    position: { x: 300, y: 570 },
    data: { label: "SQLite-vec\nLocal Vector Cache" },
    style: { ...nodeStyle("#2a2a2a"), whiteSpace: "pre-line" },
  },
];

const edgeBase = { animated: true, markerEnd: { type: MarkerType.ArrowClosed, color: "#555" } };

const initialEdges: Edge[] = [
  { id: "e-m-policy", source: "manager", target: "policy", style: { stroke: "#ffffff" }, markerEnd: { type: MarkerType.ArrowClosed, color: "#ffffff" }, animated: true },
  { id: "e-m-ebpf", source: "manager", target: "ebpf", style: { stroke: "#777" }, ...edgeBase },
  { id: "e-policy-athena", source: "policy", target: "athena", style: { stroke: "#666" }, ...edgeBase },
  { id: "e-athena-lance", source: "athena", target: "lancedb", style: { stroke: "#555" }, ...edgeBase },
  { id: "e-m-edge", source: "manager", target: "edge", style: { stroke: "#444" }, ...edgeBase },
  { id: "e-edge-sqlite", source: "edge", target: "sqlitevec", style: { stroke: "#333" }, ...edgeBase },
  { id: "e-lance-edge", source: "lancedb", target: "edge", label: "CONTEXT_HANDOFF", labelStyle: { fill: "#666", fontSize: 9, fontFamily: "var(--font-geist-mono)" }, style: { stroke: "#444" }, type: "step", ...edgeBase },
];

export function ArchitectureGraph() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="w-full h-[560px] rounded-xl bg-black/30 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        proOptions={{ hideAttribution: true }}
        colorMode="dark"
        nodesDraggable={false}
        zoomOnScroll={false}
        panOnDrag={false}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#222" />
        <Controls showInteractive={false} className="opacity-40" />
      </ReactFlow>
    </div>
  );
}
