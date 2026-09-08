/**
 * TypeScript definitions for Bitcoin Transaction Forensics Dashboard.
 */

export interface SHAPExplanation {
  feature: string;
  shap_value: number;
  direction: 'increases_risk' | 'decreases_risk';
  raw_value: number | string;
}

export interface SubgraphNode {
  id: string;
  label: string;
  type: 'wallet' | 'transaction' | 'ip' | 'target';
  in_degree?: number;
  out_degree?: number;
  country?: string;
  city?: string;
  risk_score?: number;
}

export interface SubgraphEdge {
  source: string;
  target: string;
  type: string;
  amount?: number;
  weight?: number;
}

export interface SubgraphData {
  nodes: SubgraphNode[];
  edges: SubgraphEdge[];
}

export interface EvidencePackage {
  wallet_id: string;
  final_risk_score: number;
  confidence_label: 'Critical' | 'High' | 'Medium' | 'Low' | string;
  pattern_hint: string;
  reason_sentence: string;
  shap_explanation: SHAPExplanation[];
  subgraph: SubgraphData;
  anomaly_score?: number;
  community_risk_score?: number;
  ingress_volume_btc?: number;
  egress_volume_btc?: number;
  tx_count?: number;
}

export interface NetworkSummaryStats {
  total_wallets: number;
  avg_risk_score: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_flagged_volume_btc: number;
  pattern_counts: Record<string, number>;
  country_counts: Record<string, number>;
}

export interface FilterState {
  minRiskScore: number;
  selectedSeverities: string[];
  selectedPatterns: string[];
  searchQuery: string;
}

export type TabId = 'overview' | 'queue' | 'detail' | 'network' | 'models';
