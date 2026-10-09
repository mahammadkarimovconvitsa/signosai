import { apiFetch } from "./http";
import type {
  ActionOut,
  ActionStatus,
  AlarmIngestResult,
  AlarmOut,
  AuditEventOut,
  AutonomyLevel,
  BusinessConfigOut,
  CellOut,
  CommercialSummaryOut,
  ContractOut,
  ContractSlaOut,
  CustomerImpactOut,
  FinanceSummaryOut,
  IncidentOut,
  IncidentStatus,
  IncidentTimelineEventOut,
  LinkOut,
  MarketItemOut,
  Metric,
  PaginatedResponse,
  SettingsOut,
  SiteOut,
  SitePortfolioOut,
  TokenResponse,
  UserOut,
  UserRole,
} from "./types";

export interface Pagination {
  limit?: number;
  offset?: number;
}

// --- auth ---

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
      skipAuth: true,
    }),
  me: () => apiFetch<UserOut>("/auth/me"),
};

// --- users (admin) ---

export const usersApi = {
  list: (p: Pagination = {}) =>
    apiFetch<PaginatedResponse<UserOut>>("/users", { params: p }),
  create: (email: string, password: string, role: UserRole) =>
    apiFetch<UserOut>("/users", { method: "POST", body: { email, password, role } }),
  activate: (id: string) => apiFetch<UserOut>(`/users/${id}/activate`, { method: "POST" }),
  deactivate: (id: string) => apiFetch<UserOut>(`/users/${id}/deactivate`, { method: "POST" }),
};

// --- network ---

export const networkApi = {
  listSites: (p: Pagination = {}) =>
    apiFetch<PaginatedResponse<SiteOut>>("/network/sites", { params: p }),
  getSite: (id: string) => apiFetch<SiteOut>(`/network/sites/${id}`),
  listLinks: (p: Pagination = {}) =>
    apiFetch<PaginatedResponse<LinkOut>>("/network/links", { params: p }),
  listCells: (p: Pagination & { site_id?: string } = {}) =>
    apiFetch<PaginatedResponse<CellOut>>("/network/cells", { params: p }),
};

// --- contracts ---

export const contractsApi = {
  list: (p: Pagination & { customer_id?: string } = {}) =>
    apiFetch<PaginatedResponse<ContractOut>>("/contracts", { params: p }),
  get: (id: string) => apiFetch<ContractOut>(`/contracts/${id}`),
};

// --- market ---

export const marketApi = {
  list: (p: Pagination = {}) =>
    apiFetch<PaginatedResponse<MarketItemOut>>("/market", { params: p }),
};

// --- config (admin) ---

export const configApi = {
  getSettings: () => apiFetch<SettingsOut>("/settings"),
  updateSettings: (autonomy_level: AutonomyLevel) =>
    apiFetch<SettingsOut>("/settings", { method: "PUT", body: { autonomy_level } }),
  listBusinessConfig: (p: Pagination = {}) =>
    apiFetch<PaginatedResponse<BusinessConfigOut>>("/business-config", { params: p }),
  updateBusinessConfig: (key: string, value: string, description?: string) =>
    apiFetch<BusinessConfigOut>(`/business-config/${key}`, {
      method: "PUT",
      body: { value, description },
    }),
};

// --- alarms ---

export const alarmsApi = {
  ingest: (
    alarms: Array<{
      timestamp: string;
      site_id: string;
      cell_id?: string;
      link_id?: string;
      severity: string;
      type: string;
    }>,
  ) => apiFetch<AlarmIngestResult>("/alarms/ingest", { method: "POST", body: { alarms } }),
  list: (p: Pagination & { processed?: boolean; site_id?: string } = {}) =>
    apiFetch<PaginatedResponse<AlarmOut>>("/alarms", { params: p }),
};

// --- incidents ---

export const incidentsApi = {
  list: (p: Pagination & { status?: IncidentStatus } = {}) =>
    apiFetch<PaginatedResponse<IncidentOut>>("/incidents", { params: p }),
  current: () => apiFetch<IncidentOut>("/incidents/current"),
  get: (id: string) => apiFetch<IncidentOut>(`/incidents/${id}`),
  timeline: (id: string) =>
    apiFetch<IncidentTimelineEventOut[]>(`/incidents/${id}/timeline`),
  updateEta: (id: string, eta_at: string) =>
    apiFetch<IncidentOut>(`/incidents/${id}/eta`, { method: "PUT", body: { eta_at } }),
  resolve: (id: string) =>
    apiFetch<IncidentOut>(`/incidents/${id}/resolve`, { method: "POST" }),
};

// --- analysis (impact / sla / finance / commercial, scoped to an incident) ---

export const analysisApi = {
  impact: (incidentId: string) =>
    apiFetch<CustomerImpactOut[]>(`/incidents/${incidentId}/impact`),
  sla: (incidentId: string) =>
    apiFetch<ContractSlaOut[]>(`/incidents/${incidentId}/sla`),
  finance: (incidentId: string) =>
    apiFetch<FinanceSummaryOut>(`/incidents/${incidentId}/finance`),
  commercial: (incidentId: string) =>
    apiFetch<CommercialSummaryOut>(`/incidents/${incidentId}/commercial`),
};

// --- portfolio ---

export const portfolioApi = {
  list: (p: Pagination = {}) =>
    apiFetch<PaginatedResponse<SitePortfolioOut>>("/portfolio", { params: p }),
};

// --- actions / approvals ---

export const actionsApi = {
  list: (p: Pagination & { status?: ActionStatus; incident_id?: string } = {}) =>
    apiFetch<PaginatedResponse<ActionOut>>("/actions", { params: p }),
  approve: (id: string) => apiFetch<ActionOut>(`/actions/${id}/approve`, { method: "POST" }),
  reject: (id: string) => apiFetch<ActionOut>(`/actions/${id}/reject`, { method: "POST" }),
};

// --- audit (admin) ---

export const auditApi = {
  list: (
    p: Pagination & {
      agent?: string;
      actor_role?: UserRole;
      entity?: string;
      since?: string;
      until?: string;
    } = {},
  ) => apiFetch<PaginatedResponse<AuditEventOut>>("/audit", { params: p }),
};

// --- explain ---

export const explainApi = {
  get: (metricId: string) => apiFetch<Metric>(`/explain/${encodeURIComponent(metricId)}`),
};

// --- admin ---

export const adminApi = {
  reset: () => apiFetch<void>("/admin/reset", { method: "POST" }),
};
