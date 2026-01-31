import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowDownTrayIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline'
import { exportsApi } from '../api/exports'
import { Card, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export default function Export() {
  const queryClient = useQueryClient()
  const today = new Date()
  const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
    .toISOString()
    .split('T')[0]

  const [startDate, setStartDate] = useState(firstDayOfMonth)
  const [endDate, setEndDate] = useState(today.toISOString().split('T')[0])

  const { data: pendingData } = useQuery({
    queryKey: ['exportPending'],
    queryFn: exportsApi.getPending,
  })

  const { data: exportsData, isLoading } = useQuery({
    queryKey: ['exports'],
    queryFn: () => exportsApi.list(20),
  })

  const exportMutation = useMutation({
    mutationFn: exportsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      queryClient.invalidateQueries({ queryKey: ['exportPending'] })
      alert('내보내기가 완료되었습니다.')
    },
    onError: (error: any) => {
      alert(`내보내기 실패: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleExport = () => {
    if (!startDate || !endDate) {
      alert('시작일과 종료일을 선택해주세요.')
      return
    }
    exportMutation.mutate({ start_date: startDate, end_date: endDate })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">데이터 내보내기</h1>
        <p className="text-gray-500">업무일지 데이터를 JSON으로 내보내기</p>
      </div>

      {/* Pending Count */}
      <Card className="bg-orange-50 border-orange-200">
        <div className="flex items-center gap-4">
          <div className="rounded-lg bg-orange-500 p-3">
            <DocumentArrowDownIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <p className="text-sm text-orange-700">미내보내기 데이터</p>
            <p className="text-2xl font-bold text-orange-900">
              {pendingData?.pending_count || 0}건
            </p>
          </div>
        </div>
      </Card>

      {/* Export Form */}
      <Card>
        <CardHeader title="내보내기 설정" />
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                시작일
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                종료일
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              />
            </div>
          </div>

          <Button
            onClick={handleExport}
            disabled={exportMutation.isPending}
            className="w-full"
          >
            <ArrowDownTrayIcon className="mr-2 h-4 w-4" />
            {exportMutation.isPending ? '내보내기 중...' : '내보내기 실행'}
          </Button>
        </div>
      </Card>

      {/* Export History */}
      <Card>
        <CardHeader title="내보내기 이력" />
        {isLoading ? (
          <p>로딩 중...</p>
        ) : exportsData?.exports && exportsData.exports.length > 0 ? (
          <div className="space-y-2">
            {exportsData.exports.map((exp) => (
              <div
                key={exp.export_id}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3"
              >
                <div>
                  <p className="font-medium text-gray-900">{exp.export_id}</p>
                  <p className="text-sm text-gray-500">
                    {exp.start_date} ~ {exp.end_date} | {exp.session_count}건
                  </p>
                </div>
                <a
                  href={exportsApi.download(exp.export_id)}
                  download
                  className="flex items-center gap-1 text-primary hover:underline"
                >
                  <ArrowDownTrayIcon className="h-4 w-4" />
                  다운로드
                </a>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">내보내기 이력이 없습니다.</p>
        )}
      </Card>
    </div>
  )
}
