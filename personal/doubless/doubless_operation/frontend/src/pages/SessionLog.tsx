import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import { sessionsApi } from '../api/sessions'
import { Card, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Modal } from '../components/ui/Modal'
import type { SessionLog as SessionType, SessionCreate, SessionStatus } from '../types'

export default function SessionLog() {
  const queryClient = useQueryClient()
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSession, setEditingSession] = useState<SessionType | null>(null)

  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions', selectedDate],
    queryFn: () => sessionsApi.getDaily(selectedDate),
  })

  const { data: trainersData } = useQuery({
    queryKey: ['trainers'],
    queryFn: sessionsApi.getTrainers,
  })

  const createMutation = useMutation({
    mutationFn: sessionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      setIsModalOpen(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<SessionCreate> }) =>
      sessionsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      setIsModalOpen(false)
      setEditingSession(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: sessionsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    },
  })

  const handleSubmit = (formData: SessionCreate) => {
    if (editingSession) {
      updateMutation.mutate({ id: editingSession.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (session: SessionType) => {
    setEditingSession(session)
    setIsModalOpen(true)
  }

  const handleDelete = (id: number) => {
    if (confirm('정말 삭제하시겠습니까?')) {
      deleteMutation.mutate(id)
    }
  }

  const statusLabel: Record<SessionStatus, string> = {
    completed: '완료',
    cancelled: '취소',
    no_show: '노쇼',
    payment: '결제',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">업무일지</h1>
          <p className="text-gray-500">수업 기록 관리</p>
        </div>
        <Button onClick={() => { setEditingSession(null); setIsModalOpen(true) }}>
          <PlusIcon className="mr-2 h-4 w-4" />
          수업 추가
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">날짜</label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2"
            />
          </div>
        </div>
      </Card>

      {/* Sessions Table */}
      <Card>
        <CardHeader title={`${selectedDate} 수업 목록`} />
        {isLoading ? (
          <p>로딩 중...</p>
        ) : sessions && sessions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b text-left text-sm text-gray-500">
                  <th className="pb-3 font-medium">시간</th>
                  <th className="pb-3 font-medium">트레이너</th>
                  <th className="pb-3 font-medium">회원</th>
                  <th className="pb-3 font-medium">타입</th>
                  <th className="pb-3 font-medium">진도</th>
                  <th className="pb-3 font-medium">상태</th>
                  <th className="pb-3 font-medium">액션</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((session) => (
                  <tr key={session.id} className="border-b last:border-0">
                    <td className="py-3">{session.session_time}</td>
                    <td className="py-3">{session.trainer_name}</td>
                    <td className="py-3">{session.member_name}</td>
                    <td className="py-3">
                      {session.session_type}
                      {session.is_event && (
                        <span className="ml-1 text-xs text-orange-500">(이벤트)</span>
                      )}
                    </td>
                    <td className="py-3">{session.session_index || '-'}</td>
                    <td className="py-3">
                      <span
                        className={`badge ${
                          session.session_status === 'completed'
                            ? 'badge-success'
                            : session.session_status === 'cancelled'
                            ? 'badge-danger'
                            : 'badge-warning'
                        }`}
                      >
                        {statusLabel[session.session_status]}
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(session)}
                          className="p-1 text-gray-400 hover:text-primary"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(session.id)}
                          className="p-1 text-gray-400 hover:text-red-500"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">등록된 수업이 없습니다.</p>
        )}
      </Card>

      {/* Session Modal */}
      <SessionModal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingSession(null) }}
        onSubmit={handleSubmit}
        initialData={editingSession}
        selectedDate={selectedDate}
        trainers={trainersData?.trainers || []}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  )
}

interface SessionModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: SessionCreate) => void
  initialData: SessionType | null
  selectedDate: string
  trainers: string[]
  isLoading: boolean
}

function SessionModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  selectedDate,
  trainers,
  isLoading,
}: SessionModalProps) {
  const [formData, setFormData] = useState<SessionCreate>({
    session_date: selectedDate,
    session_time: '',
    trainer_name: '',
    member_name: '',
    session_type: 'PT',
    session_status: 'completed',
    session_index: '',
    is_event: false,
    note: '',
  })

  // Reset form when modal opens
  useState(() => {
    if (initialData) {
      setFormData({
        session_date: initialData.session_date,
        session_time: initialData.session_time,
        trainer_name: initialData.trainer_name,
        member_name: initialData.member_name,
        session_type: initialData.session_type,
        session_status: initialData.session_status,
        session_index: initialData.session_index || '',
        is_event: initialData.is_event,
        note: initialData.note || '',
      })
    } else {
      setFormData({
        session_date: selectedDate,
        session_time: '',
        trainer_name: '',
        member_name: '',
        session_type: 'PT',
        session_status: 'completed',
        session_index: '',
        is_event: false,
        note: '',
      })
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? '수업 수정' : '수업 추가'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">날짜</label>
            <input
              type="date"
              value={formData.session_date}
              onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">시간</label>
            <input
              type="time"
              value={formData.session_time}
              onChange={(e) => setFormData({ ...formData, session_time: e.target.value })}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">트레이너</label>
          <input
            type="text"
            value={formData.trainer_name}
            onChange={(e) => setFormData({ ...formData, trainer_name: e.target.value })}
            list="trainer-list"
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
            placeholder="트레이너 이름"
            required
          />
          <datalist id="trainer-list">
            {trainers.map((t) => (
              <option key={t} value={t} />
            ))}
          </datalist>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">회원</label>
          <input
            type="text"
            value={formData.member_name}
            onChange={(e) => setFormData({ ...formData, member_name: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
            placeholder="회원 이름"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">타입</label>
            <select
              value={formData.session_type}
              onChange={(e) => setFormData({ ...formData, session_type: e.target.value })}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            >
              <option value="PT">PT</option>
              <option value="OT">OT</option>
              <option value="기타">기타</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
            <select
              value={formData.session_status}
              onChange={(e) => setFormData({ ...formData, session_status: e.target.value as SessionStatus })}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            >
              <option value="completed">완료</option>
              <option value="cancelled">취소</option>
              <option value="no_show">노쇼</option>
              <option value="payment">결제</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">진도 (예: 15/20)</label>
          <input
            type="text"
            value={formData.session_index}
            onChange={(e) => setFormData({ ...formData, session_index: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
            placeholder="15/20"
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_event"
            checked={formData.is_event}
            onChange={(e) => setFormData({ ...formData, is_event: e.target.checked })}
            className="h-4 w-4 rounded border-gray-300"
          />
          <label htmlFor="is_event" className="text-sm text-gray-700">이벤트권</label>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">메모</label>
          <textarea
            value={formData.note}
            onChange={(e) => setFormData({ ...formData, note: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
            rows={2}
          />
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            취소
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? '저장 중...' : '저장'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
