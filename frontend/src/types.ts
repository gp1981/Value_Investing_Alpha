export interface StockItem {
  rank: number;
  ticker: string;
  company_name: string;
  sector: string;
  sic_code?: number | null;
  price: number;
  market_cap: number;
  enterprise_value: number;
  ebit: number;
  earnings_yield: number;
  return_on_capital: number;
  magic_formula_rank?: number | null;
  reproduction_value_per_share?: number | null;
  epv_per_share?: number | null;
  epv_margin_of_safety?: number | null;
  traffic_light: 'GREEN' | 'YELLOW' | 'RED';
  wc_anomaly: string;
  fcff_ttm?: number | null;
  mc_to_fcff_ttm?: number | null;
  mc_to_fcff_5y_avg?: number | null;
}

export interface ScreenerResponse {
  total_count: number;
  returned_count: number;
  source: string;
  timestamp: string;
  items: StockItem[];
}

export interface MagicFormulaDetails {
  ebit: number;
  enterprise_value: number;
  earnings_yield: number;
  tangible_capital_employed: number;
  return_on_capital: number;
  excess_cash: number;
}

export interface GreenwaldDetails {
  reproduction_value: number;
  reproduction_value_per_share: number;
  epv: number;
  epv_per_share: number;
  wacc: number;
  tax_rate: number;
  franchise_factor: number;
  margin_of_safety: number;
}

export interface DCFDetails {
  intrinsic_value: number;
  intrinsic_value_per_share: number;
  discount_rate: number;
  growth_rate: number;
  margin_of_safety: number;
}

export interface SafetyDetails {
  traffic_light: string;
  quick_ratio: number;
  debt_to_equity: number;
  debt_to_assets: number;
  revenue_zscore_label: string;
  wc_anomaly_signal: string;
}

export interface SECFilingItem {
  form: string;
  filing_date: string;
  report_date?: string | null;
  accession_number: string;
  description?: string;
  url: string;
  interactive_url?: string | null;
}

export interface HorizonMetric {
  horizon: string;
  price_return_pct?: number | null;
  dividend_yield_pct?: number | null;
  total_return_pct?: number | null;
  roic_pct?: number | null;
  revenue_cagr_pct?: number | null;
  fcff?: number | null;
  mc_to_fcff?: number | null;
}

export interface CompanyDetailResponse {
  ticker: string;
  company_name: string;
  description?: string;
  sic_code?: number | null;
  industry?: string;
  price: number;
  market_cap: number;
  shares_outstanding: number;
  magic_formula: MagicFormulaDetails;
  greenwald: GreenwaldDetails;
  dcf: DCFDetails;
  safety: SafetyDetails;
  financial_statement: Record<string, any>;
  filings?: SECFilingItem[];
  data_source?: string;
  fcff_ttm?: number | null;
  mc_to_fcff_ttm?: number | null;
  fcff_5y_avg?: number | null;
  mc_to_fcff_5y_avg?: number | null;
  horizon_metrics?: HorizonMetric[];
}

export interface StatementRow {
  concept: string;
  label: string;
  depth: number;
  is_abstract: boolean;
  is_total: boolean;
  values: Record<string, number | null>;
}

export interface StatementReport {
  periods: string[];
  rows: StatementRow[];
}

export interface CompanyStatementsResponse {
  ticker: string;
  company_name: string;
  balance_sheet?: StatementReport | null;
  income_statement?: StatementReport | null;
  cash_flow?: StatementReport | null;
  quarterly_balance_sheet?: StatementReport | null;
  quarterly_income_statement?: StatementReport | null;
  quarterly_cash_flow?: StatementReport | null;
  shares_by_period?: Record<string, number>;
  latest_floating_shares?: number | null;
}

export interface NonRecurringItem {
  category: string;
  label: string;
  amount?: number | null;
  period: string;
  note: string;
}

export interface NonRecurringResponse {
  ticker: string;
  capex_to_da_ratio?: number | null;
  estimated_maintenance_capex?: number | null;
  estimated_growth_capex?: number | null;
  items: NonRecurringItem[];
}

export interface SeasonalityQuarterPoint {
  period: string;
  fiscal_quarter: string;
  fiscal_year: string;
  revenue?: number | null;
  inventory?: number | null;
}

export interface SeasonalityResponse {
  ticker: string;
  points: SeasonalityQuarterPoint[];
  quarter_averages: Record<string, { avg_revenue?: number | null; avg_inventory?: number | null }>;
}

export interface FilingSectionItem {
  id: string;
  title: string;
}

export interface FilingAttachmentItem {
  document: string;
  description: string;
  doc_type: string;
  url: string;
}

export interface FilingContentResponse {
  ticker: string;
  accession_number: string;
  form: string;
  filing_date: string;
  report_date?: string | null;
  available_sections: string[];
  section_bookmarks?: FilingSectionItem[];
  attachments?: FilingAttachmentItem[];
  selected_section?: string | null;
  content: string;
  sec_url: string;
}

export interface EdgarFormItem {
  form: string;
  object_name: string;
  category: string;
  description: string;
}

export interface DiffToken {
  type: 'equal' | 'added' | 'removed';
  text: string;
}

export interface FilingDiffResponse {
  ticker: string;
  form: string;
  section: string;
  accession_1: string;
  accession_2: string;
  date_1: string;
  date_2: string;
  similarity_pct: number;
  words_added: number;
  words_removed: number;
  tokens: DiffToken[];
}

export interface InsiderTransactionItem {
  filing_date: string;
  transaction_date: string;
  insider_name: string;
  title: string;
  transaction_code: string;
  shares: number;
  price?: number | null;
  value_usd?: number | null;
  sec_url: string;
}

export interface InsiderRadarResponse {
  ticker: string;
  cluster_buying_detected: boolean;
  cluster_buyers_count: number;
  total_purchases_usd: number;
  total_sales_usd: number;
  transactions: InsiderTransactionItem[];
}

export interface MaterialEventItem {
  filing_date: string;
  accession_number: string;
  items: string[];
  summary: string;
  sec_url: string;
}

export interface MaterialEventsResponse {
  ticker: string;
  events: MaterialEventItem[];
}

export interface GovernanceResponse {
  ticker: string;
  filing_date: string;
  accession_number: string;
  sec_url: string;
  summary: string;
  compensation_rows: Record<string, unknown>[];
}

export interface FilingSearchHit {
  section: string;
  snippet: string;
}

export interface FilingSearchResponse {
  ticker: string;
  form: string;
  filing_date: string;
  accession_number: string;
  query: string;
  total_hits: number;
  hits: FilingSearchHit[];
}

export interface SuperinvestorProfile {
  cik: string;
  manager: string;
  fund_name: string;
  style: string;
  note?: string | null;
}

export interface SuperinvestorHolding {
  cusip: string;
  ticker?: string | null;
  issuer: string;
  shares: number;
  value_usd: number;
  weight_pct: number;
  activity: string;
  share_change_pct?: number | null;
}

export interface SuperinvestorPortfolioResponse {
  cik: string;
  manager: string;
  fund_name: string;
  style: string;
  filing_date: string;
  report_period: string;
  previous_report_period?: string | null;
  total_value_usd: number;
  holdings_count: number;
  sec_url: string;
  holdings: SuperinvestorHolding[];
  source: string;
}
