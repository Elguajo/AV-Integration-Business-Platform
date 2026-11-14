// Shapes returned by av_platform.sales_api. The server owns every decision;
// the client only renders these values.

export type Stage =
  | 'draft'
  | 'issued'
  | 'superseded'
  | 'handover_draft'
  | 'handover_pending'
  | 'returned'
  | 'accepted'
  | 'handover_unknown'
  | 'cancelled'

export type Blocker =
  | 'not_submitted'
  | 'not_current_version'
  | 'not_customer'
  | 'no_main_items'
  | 'handover_exists'
  | 'no_permission'

export interface Handover {
  name: string
  quotation: string
  review_status: 'Pending' | 'Accepted' | 'Returned'
  docstatus: number
  project: string | null
  project_manager: string
  project_manager_name?: string
  reviewed_on: string | null
  review_note: string | null
  accepted_value: number | null
  currency: string | null
  creation: string
}

export interface QuotationRow {
  name: string
  title: string | null
  party_name: string
  customer_name: string | null
  status: string
  docstatus: number
  grand_total: number | null
  currency: string | null
  transaction_date: string | null
  valid_till: string | null
  modified: string
  stage: Stage
  handover: Handover | null
}

export interface Workspace {
  user: { name: string; full_name: string }
  quotations: QuotationRow[]
}

export interface Line {
  idx: number
  item_code: string
  item_name: string | null
  qty: number
  uom: string | null
  rate: number
  amount: number
  is_alternative: boolean
}

export interface Version {
  name: string
  title: string | null
  docstatus: number
  status: string
  grand_total: number | null
  currency: string | null
  version: number
  is_current: boolean
}

export interface QuotationDetail {
  quotation: {
    name: string
    title: string | null
    party_name: string
    customer_name: string | null
    status: string
    docstatus: number
    currency: string | null
    transaction_date: string | null
    valid_till: string | null
    grand_total: number | null
    total_taxes_and_charges: number | null
    terms: string | null
  }
  stage: Stage
  main_items: Line[]
  alternatives: Line[]
  main_total: number
  versions: Version[]
  handover: Handover | null
  can_handover: boolean
  blockers: Blocker[]
  pm_options: { name: string; full_name: string | null }[]
}

export const API = {
  workspace: '/api/v2/method/av_platform.sales_api.get_workspace',
  quotation: '/api/v2/method/av_platform.sales_api.get_quotation',
  createHandover: '/api/v2/method/av_platform.sales_api.create_handover',
}
