export interface Transaction {
  id: string;
  fileId: string;
  rawData: string;
  entities: Entity[];
  riskScore: number;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  createdAt: Date;
  updatedAt: Date;
}

export interface Entity {
  id: string;
  name: string;
  type: 'INDIVIDUAL' | 'ORGANIZATION' | 'LOCATION';
  role: 'PAYER' | 'RECEIVER' | 'INTERMEDIARY';
  enrichmentData: {
    sec?: SECData;
    ofac?: OFACData;
    media?: MediaData;
    regulatory?: RegulatoryData;
    legal?: LegalData;
  };
  riskScore: number;
}

export interface SECData {
  cik: string;
  filings: any[];
  status: string;
}

export interface OFACData {
  sanctioned: boolean;
  listEntries: any[];
  lastChecked: Date;
}

export interface MediaData {
  sentiment: number;
  articles: any[];
  lastUpdated: Date;
}

export interface RegulatoryData {
  status: string;
  violations: any[];
  lastChecked: Date;
}

export interface LegalData {
  cases: any[];
  status: string;
  lastUpdated: Date;
}

export interface FileMetadata {
  id: string;
  filename: string;
  size: number;
  format: 'JSON' | 'CSV' | 'EXCEL' | 'XML' | 'PDF' | 'TXT';
  uploadedBy: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  createdAt: Date;
  updatedAt: Date;
}

export interface TransactionStatistics {
  totalCount: number;
  highRiskCount: number;
  mediumRiskCount: number;
  lowRiskCount: number;
  averageRiskScore: number;
  totalAmount: number;
  complianceRate: number;
}

export interface TransactionResponse {
  transactionId: string;
  extractedEntities: string[];
  entityTypes: string[];
  riskScore: number;
  supportingEvidence: string[];
  confidenceScore: number;
  reason: string;
}