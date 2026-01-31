import { Outlet, NavLink } from 'react-router-dom'
import {
  HomeIcon,
  ClipboardDocumentListIcon,
  UsersIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline'

const navigation = [
  { name: '대시보드', href: '/', icon: HomeIcon },
  { name: '업무일지', href: '/sessions', icon: ClipboardDocumentListIcon },
  { name: '회원/수강권', href: '/members', icon: UsersIcon },
  { name: '내보내기', href: '/export', icon: ArrowDownTrayIcon },
]

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-sidebar">
        <div className="flex h-16 items-center justify-center border-b border-gray-700">
          <h1 className="text-xl font-bold text-white">더블에스 운영</h1>
        </div>
        <nav className="mt-6 px-3">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary text-white'
                    : 'text-gray-300 hover:bg-sidebar-hover hover:text-white'
                }`
              }
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="ml-64 min-h-screen p-6">
        <Outlet />
      </main>
    </div>
  )
}
