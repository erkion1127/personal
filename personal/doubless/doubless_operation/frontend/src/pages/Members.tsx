import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowPathIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { membersApi } from '../api/members'
import { Card, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import apiClient from '../api/client'
import type { LessonTicket } from '../types'

export default function Members() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'members' | 'tickets'>('members')

  // Members
  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: ['members'],
    queryFn: () => membersApi.list({ limit: 100 }),
  })

  const { data: memberStats } = useQuery({
    queryKey: ['memberStats'],
    queryFn: membersApi.getStats,
  })

  const memberSyncMutation = useMutation({
    mutationFn: membersApi.sync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] })
      queryClient.invalidateQueries({ queryKey: ['memberStats'] })
    },
  })

  // Lesson Tickets
  const { data: ticketsData, isLoading: ticketsLoading } = useQuery({
    queryKey: ['lessonTickets'],
    queryFn: async () => {
      const response = await apiClient.get<LessonTicket[]>('/lesson-tickets')
      return response.data
    },
  })

  const ticketSyncMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/lesson-tickets/sync')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lessonTickets'] })
    },
  })

  // Search
  const { data: searchResults } = useQuery({
    queryKey: ['memberSearch', searchQuery],
    queryFn: () => membersApi.search(searchQuery),
    enabled: searchQuery.length >= 2,
  })

  const filteredMembers = searchQuery.length >= 2
    ? searchResults?.members
    : membersData

  const filteredTickets = searchQuery.length >= 2
    ? ticketsData?.filter((t) =>
        t.member_name.includes(searchQuery) ||
        t.trainer_name?.includes(searchQuery)
      )
    : ticketsData

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">회원 / 수강권</h1>
          <p className="text-gray-500">CRM 데이터 동기화 및 조회</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={() => memberSyncMutation.mutate()}
            disabled={memberSyncMutation.isPending}
          >
            <ArrowPathIcon className={`mr-2 h-4 w-4 ${memberSyncMutation.isPending ? 'animate-spin' : ''}`} />
            회원 동기화
          </Button>
          <Button
            onClick={() => ticketSyncMutation.mutate()}
            disabled={ticketSyncMutation.isPending}
          >
            <ArrowPathIcon className={`mr-2 h-4 w-4 ${ticketSyncMutation.isPending ? 'animate-spin' : ''}`} />
            수강권 동기화
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <p className="text-sm text-gray-500">캐시된 회원</p>
          <p className="text-2xl font-bold">{memberStats?.total || 0}명</p>
          {memberStats?.synced_at && (
            <p className="text-xs text-gray-400 mt-1">
              마지막 동기화: {new Date(memberStats.synced_at).toLocaleString('ko-KR')}
            </p>
          )}
        </Card>
        <Card>
          <p className="text-sm text-gray-500">활성 수강권</p>
          <p className="text-2xl font-bold">{ticketsData?.length || 0}건</p>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="회원명 또는 전화번호 검색..."
              className="w-full rounded-lg border border-gray-300 pl-10 pr-4 py-2"
            />
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-8">
          <button
            onClick={() => setActiveTab('members')}
            className={`pb-3 text-sm font-medium ${
              activeTab === 'members'
                ? 'border-b-2 border-primary text-primary'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            회원 목록
          </button>
          <button
            onClick={() => setActiveTab('tickets')}
            className={`pb-3 text-sm font-medium ${
              activeTab === 'tickets'
                ? 'border-b-2 border-primary text-primary'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            수강권 목록
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'members' ? (
        <Card>
          <CardHeader title="회원 목록" />
          {membersLoading ? (
            <p>로딩 중...</p>
          ) : filteredMembers && filteredMembers.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">이름</th>
                    <th className="pb-3 font-medium">연락처</th>
                    <th className="pb-3 font-medium">담당 트레이너</th>
                    <th className="pb-3 font-medium">잔여 PT</th>
                  </tr>
                </thead>
                <tbody>
                  {(filteredMembers as any[]).slice(0, 50).map((member) => (
                    <tr key={member.jgjm_key || member.id} className="border-b last:border-0">
                      <td className="py-3">{member.name}</td>
                      <td className="py-3 text-gray-500">{member.phone || '-'}</td>
                      <td className="py-3">{member.trainer_name || '-'}</td>
                      <td className="py-3">{member.pt_remaining ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">
              {searchQuery ? '검색 결과가 없습니다.' : '회원 데이터가 없습니다. 동기화를 실행해주세요.'}
            </p>
          )}
        </Card>
      ) : (
        <Card>
          <CardHeader title="수강권 목록 (잔여 횟수 있는 것만)" />
          {ticketsLoading ? (
            <p>로딩 중...</p>
          ) : filteredTickets && filteredTickets.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">회원</th>
                    <th className="pb-3 font-medium">수강권</th>
                    <th className="pb-3 font-medium">잔여/총</th>
                    <th className="pb-3 font-medium">담당</th>
                    <th className="pb-3 font-medium">종료일</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTickets.slice(0, 50).map((ticket) => (
                    <tr key={ticket.jglesson_ticket_key} className="border-b last:border-0">
                      <td className="py-3">{ticket.member_name}</td>
                      <td className="py-3">{ticket.ticket_type}</td>
                      <td className="py-3">
                        <span className="font-medium text-primary">{ticket.remaining_count}</span>
                        <span className="text-gray-400">/{ticket.total_count}</span>
                      </td>
                      <td className="py-3">{ticket.trainer_name || '-'}</td>
                      <td className="py-3 text-gray-500">{ticket.end_date || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">
              수강권 데이터가 없습니다. 동기화를 실행해주세요.
            </p>
          )}
        </Card>
      )}
    </div>
  )
}
