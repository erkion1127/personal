// Session Types
export interface SessionLog {
  id: number
  session_date: string
  session_time: string
  trainer_name: string
  member_name: string
  member_key?: number
  session_type: string
  session_status: SessionStatus
  session_index?: string
  is_event: boolean
  registration_type?: string
  note?: string
  created_at: string
  exported: boolean
}

export type SessionStatus = 'completed' | 'cancelled' | 'no_show' | 'payment'

export interface SessionCreate {
  session_date: string
  session_time: string
  trainer_name: string
  member_name: string
  member_key?: number
  session_type?: string
  session_status?: SessionStatus
  session_index?: string
  is_event?: boolean
  registration_type?: string
  note?: string
}

// Member Types
export interface Member {
  id: number
  jgjm_key: number
  name: string
  phone?: string
  gender?: string
  trainer_name?: string
  pt_remaining?: number
  pt_total?: number
  membership_end?: string
  classification?: string
  customer_status?: string
  synced_at: string
}

export interface MemberSearchResult {
  jgjm_key: number
  name: string
  phone?: string
  trainer_name?: string
  pt_remaining?: number
}

// Trainer/Staff Types
export interface Trainer {
  id: number
  name: string
  phone?: string
  status: 'active' | 'inactive'
  created_at: string
}

export interface Staff {
  id: number
  name: string
  role: string
  phone?: string
  status: 'active' | 'inactive'
  created_at: string
}

// Lesson Ticket Types
export interface LessonTicket {
  jglesson_ticket_key: number
  jgjm_key: number
  member_name: string
  ticket_type: string
  total_count: number
  remaining_count: number
  trainer_name?: string
  start_date?: string
  end_date?: string
}

// Export Types
export interface ExportLog {
  id: number
  export_id: string
  export_date: string
  start_date: string
  end_date: string
  session_count: number
  file_path: string
  file_size_bytes: number
  status: string
  created_at: string
}

export interface ExportRequest {
  start_date: string
  end_date: string
}

// Dashboard Types
export interface DashboardData {
  date: string
  sessions: {
    total: number
    completed: number
    cancelled: number
    no_show: number
  }
  pending_export: number
  members_cached: number
  recent_sessions: {
    id: number
    time: string
    trainer: string
    member: string
    status: string
  }[]
}
