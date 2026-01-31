import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  ClipboardDocumentListIcon,
  ArrowDownTrayIcon,
  UsersIcon,
  PlusIcon,
} from '@heroicons/react/24/outline'
import { dashboardApi } from '../api/dashboard'
import { Card, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getToday,
    refetchInterval: 30000, // 30초마다 갱신
  })

  if (isLoading) {
    return <div className="p-6">로딩 중...</div>
  }

  const stats = [
    {
      name: '오늘 수업',
      value: data?.sessions.total || 0,
      sub: `완료 ${data?.sessions.completed || 0}건`,
      icon: ClipboardDocumentListIcon,
      color: 'bg-blue-500',
    },
    {
      name: '미내보내기',
      value: data?.pending_export || 0,
      sub: '건',
      icon: ArrowDownTrayIcon,
      color: 'bg-orange-500',
    },
    {
      name: '캐시된 회원',
      value: data?.members_cached || 0,
      sub: '명',
      icon: UsersIcon,
      color: 'bg-green-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
        <p className="text-gray-500">{data?.date}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        {stats.map((stat) => (
          <Card key={stat.name} className="card-hover">
            <div className="flex items-center gap-4">
              <div className={`rounded-lg ${stat.color} p-3`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stat.value}
                  <span className="ml-1 text-sm font-normal text-gray-500">
                    {stat.sub}
                  </span>
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader title="빠른 액션" />
        <div className="flex gap-3">
          <Link to="/sessions">
            <Button>
              <PlusIcon className="mr-2 h-4 w-4" />
              수업 기록
            </Button>
          </Link>
          <Link to="/members">
            <Button variant="secondary">회원 동기화</Button>
          </Link>
          <Link to="/export">
            <Button variant="secondary">데이터 내보내기</Button>
          </Link>
        </div>
      </Card>

      {/* Today's Sessions */}
      <Card>
        <CardHeader
          title="오늘 수업"
          action={
            <Link to="/sessions" className="text-sm text-primary hover:underline">
              전체 보기
            </Link>
          }
        />
        {data?.recent_sessions && data.recent_sessions.length > 0 ? (
          <div className="space-y-2">
            {data.recent_sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3"
              >
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium text-gray-900">
                    {session.time}
                  </span>
                  <span className="text-sm text-gray-600">{session.trainer}</span>
                  <span className="text-sm text-gray-900">{session.member}</span>
                </div>
                <span
                  className={`badge ${
                    session.status === 'completed'
                      ? 'badge-success'
                      : session.status === 'cancelled'
                      ? 'badge-danger'
                      : 'badge-warning'
                  }`}
                >
                  {session.status === 'completed'
                    ? '완료'
                    : session.status === 'cancelled'
                    ? '취소'
                    : '노쇼'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">오늘 등록된 수업이 없습니다.</p>
        )}
      </Card>
    </div>
  )
}
