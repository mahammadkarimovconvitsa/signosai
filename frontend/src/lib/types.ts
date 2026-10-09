// Mirrors backend/app/schemas/*.py and backend/app/models/enums.py exactly.

export type UserRole = "admin" | "engineer" | "account_manager" | "viewer";
export type OperationalStatus = "up" | "down";
export type CellTechnology = "4G" | "5G";
export type LinkType = "fiber" | "microwave";
export type ContractType = "enterprise_sla" | "tower_lease" | "interconnect" | "vendor_sla";
export type AlarmSeverity = "critical" | "major" | "minor" | "warning";
export type IncidentStatus = "open" | "resolved";
export type ActionAgent = "network" | "contracts" | "finance" | "commercial";
export type ActionStatus = "proposed" | "approved" | "rejected" | "executed";
export type RiskLevel = "low" | "medium" | "high";
export type AutonomyLevel = "recommend_only" | "approve_to_act" | "auto_low_risk";
export type MarketItemType = "competitor_tariff" | "regulator" | "spectrum";
export type ComplianceStatus = "ok" | "at_risk" | "breached";
export type SubscriberSegment = "premium" | "standard" | "budget";
export type PortfolioRecommendation = "upgrade" | "keep" | "consolidate" | "decommission";

export interface SourceRef {
  table: string;
  id: string;
}

export interface Metric<V = number | string> {
  value: V;
  unit: string;
  formula: string;
  inputs: Record<string, unknown>;
  sources: SourceRef[];
}

export interface PaginatedResponse<T> {
  total: number;
  limit: number;
  offset: number;
  items: T[];
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export interface UserOut {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface SiteOut {
  id: string;
  name: string;
  lat: number;
  lng: number;
  district: string;
  uplink_link_id: string | null;
  energy_cost_azn_month: number;
  status: OperationalStatus;
}

export interface LinkOut {
  id: string;
  from_site_id: string;
  to_site_id: string;
  type: LinkType;
  is_protected: boolean;
  status: OperationalStatus;
}

export interface CellOut {
  id: string;
  site_id: string;
  technology: CellTechnology;
  revenue_per_min_azn: number;
  status: OperationalStatus;
}

export interface ContractOut {
  id: string;
  customer_id: string;
  type: ContractType;
  restore_within_min: number;
  penalty_per_started_hour_azn: number;
  penalty_cap_azn: number;
  clause_text: string;
  valid_from: string;
  valid_to: string | null;
}

export interface MarketItemOut {
  id: string;
  type: MarketItemType;
  title: string;
  summary: string;
  source: string;
  published_at: string;
}

export interface SettingsOut {
  id: string;
  autonomy_level: AutonomyLevel;
}

export interface BusinessConfigOut {
  id: string;
  key: string;
  value: string;
  description: string | null;
}

export interface AlarmOut {
  id: string;
  timestamp: string;
  site_id: string;
  cell_id: string | null;
  link_id: string | null;
  severity: AlarmSeverity;
  type: string;
  processed: boolean;
  incident_id: string | null;
}

export interface AlarmIngestResult {
  ingested: number;
  incident_id: string | null;
}

export interface IncidentOut {
  id: string;
  root_cause_link_id: string;
  root_cause_summary: string | null;
  status: IncidentStatus;
  started_at: string;
  eta_at: string | null;
  resolved_at: string | null;
  alarm_count: number;
  affected_sites: SiteOut[];
}

export interface IncidentTimelineEventOut {
  id: string;
  ts: string;
  label: string;
  detail: string;
}

export interface ContractSlaOut {
  contract_id: string;
  customer_id: string;
  deadline: Metric<string>;
  time_remaining_min: Metric<number>;
  compliance_status: ComplianceStatus;
  penalty_accrued_so_far_azn: Metric<number>;
  projected_penalty_at_eta_azn: Metric<number> | null;
  worst_case_penalty_azn: Metric<number>;
}

export interface EnterpriseCustomerOut {
  id: string;
  name: string;
  sector: string;
  account_manager_user_id: string | null;
}

export interface CustomerImpactOut {
  customer: EnterpriseCustomerOut;
  contracts: ContractSlaOut[];
}

export interface FinanceSummaryOut {
  incident_id: string;
  revenue_per_min_azn: Metric<number>;
  lost_revenue_azn: Metric<number>;
  projected_penalties_azn: Metric<number>;
  compensation_cost_azn: Metric<number>;
  total_exposure_azn: Metric<number>;
}

export interface SubscriberOut {
  id: string;
  home_cell_id: string;
  segment: SubscriberSegment;
  msisdn_masked: string;
  name: string | null;
}

export interface CommercialSummaryOut {
  incident_id: string;
  affected_premium_subscribers: Metric<number>;
  compensation_cost_azn: Metric<number>;
  sample_subscribers: SubscriberOut[];
}

export interface SitePortfolioOut {
  site_id: string;
  site_name: string;
  traffic_proxy_subscribers: Metric<number>;
  revenue_azn_month: Metric<number>;
  energy_cost_azn_month: Metric<number>;
  revenue_to_cost_ratio: Metric<number>;
  recommendation: PortfolioRecommendation;
}

export interface ActionOut {
  id: string;
  incident_id: string;
  agent: ActionAgent;
  proposal: string;
  owner_role: UserRole;
  status: ActionStatus;
  risk_level: RiskLevel;
  sources: Record<string, unknown>[];
  approved_by_user_id: string | null;
  approved_at: string | null;
}

export interface AuditEventOut {
  id: string;
  timestamp: string;
  actor_user_id: string | null;
  actor_role: UserRole | null;
  event_type: string;
  entity: string;
  entity_id: string | null;
  details: Record<string, unknown>;
}
