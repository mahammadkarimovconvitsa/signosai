// Must match the "<domain>.<field>:<param1>[:<param2>]" format parsed by
// backend/app/services/explain_service.py exactly.

export const metricIds = {
  financeRevenuePerMin: (incidentId: string) => `finance.revenue_per_min:${incidentId}`,
  financeLostRevenue: (incidentId: string) => `finance.lost_revenue:${incidentId}`,
  financeProjectedPenalties: (incidentId: string) => `finance.projected_penalties:${incidentId}`,
  financeTotalExposure: (incidentId: string) => `finance.total_exposure:${incidentId}`,

  commercialAffectedPremium: (incidentId: string) =>
    `commercial.affected_premium_subscribers:${incidentId}`,
  commercialCompensationCost: (incidentId: string) =>
    `commercial.compensation_cost:${incidentId}`,

  slaDeadline: (incidentId: string, contractId: string) =>
    `sla.deadline:${incidentId}:${contractId}`,
  slaTimeRemaining: (incidentId: string, contractId: string) =>
    `sla.time_remaining:${incidentId}:${contractId}`,
  slaPenaltyAccrued: (incidentId: string, contractId: string) =>
    `sla.penalty_accrued:${incidentId}:${contractId}`,
  slaProjectedPenaltyAtEta: (incidentId: string, contractId: string) =>
    `sla.projected_penalty_at_eta:${incidentId}:${contractId}`,
  slaWorstCasePenalty: (incidentId: string, contractId: string) =>
    `sla.worst_case_penalty:${incidentId}:${contractId}`,

  portfolioTraffic: (siteId: string) => `portfolio.traffic:${siteId}`,
  portfolioRevenue: (siteId: string) => `portfolio.revenue:${siteId}`,
  portfolioEnergyCost: (siteId: string) => `portfolio.energy_cost:${siteId}`,
  portfolioRatio: (siteId: string) => `portfolio.ratio:${siteId}`,
};
