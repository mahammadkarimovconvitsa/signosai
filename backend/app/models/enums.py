import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    ACCOUNT_MANAGER = "account_manager"
    VIEWER = "viewer"


class OperationalStatus(str, enum.Enum):
    UP = "up"
    DOWN = "down"


class CellTechnology(str, enum.Enum):
    FOUR_G = "4G"
    FIVE_G = "5G"


class LinkType(str, enum.Enum):
    FIBER = "fiber"
    MICROWAVE = "microwave"


class SubscriberSegment(str, enum.Enum):
    PREMIUM = "premium"
    STANDARD = "standard"
    BUDGET = "budget"


class CustomerServiceType(str, enum.Enum):
    LEASED_LINE = "leased_line"
    PRIVATE_APN = "private_apn"
    MOBILE = "mobile"


class ContractType(str, enum.Enum):
    ENTERPRISE_SLA = "enterprise_sla"
    TOWER_LEASE = "tower_lease"
    INTERCONNECT = "interconnect"
    VENDOR_SLA = "vendor_sla"


class AlarmSeverity(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    WARNING = "warning"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class ActionAgent(str, enum.Enum):
    NETWORK = "network"
    CONTRACTS = "contracts"
    FINANCE = "finance"
    COMMERCIAL = "commercial"


class ActionStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AgentOutputSource(str, enum.Enum):
    LIVE = "live"
    FALLBACK = "fallback"


class AutonomyLevel(str, enum.Enum):
    RECOMMEND_ONLY = "recommend_only"
    APPROVE_TO_ACT = "approve_to_act"
    AUTO_LOW_RISK = "auto_low_risk"


class MarketItemType(str, enum.Enum):
    COMPETITOR_TARIFF = "competitor_tariff"
    REGULATOR = "regulator"
    SPECTRUM = "spectrum"


class ComplianceStatus(str, enum.Enum):
    OK = "ok"
    AT_RISK = "at_risk"
    BREACHED = "breached"
