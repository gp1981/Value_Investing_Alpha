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
}

export interface FilingContentResponse {
  ticker: string;
  accession_number: string;
  form: string;
  filing_date: string;
  report_date?: string | null;
  available_sections: string[];
  selected_section?: string | null;
  content: string;
  sec_url: string;
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
