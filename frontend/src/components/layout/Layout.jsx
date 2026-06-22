import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Tag, Footprints, Store, Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import ThemeToggle from '@/components/ThemeToggle'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/deals', label: 'Deals', icon: Tag },
  { to: '/shoes', label: 'Shoes', icon: Footprints },
  { to: '/retailers', label: 'Retailers', icon: Store },
]

function NavLinks({ onNavigate }) {
  return (
    <nav className="flex flex-col gap-1">
      {navItems.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
            )
          }
        >
          <Icon className="h-4 w-4" />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

function Brand() {
  return (
    <div className="flex items-center gap-2 px-3 py-1">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Footprints className="h-5 w-5" />
      </div>
      <div className="leading-tight">
        <p className="text-sm font-bold">Shoe Deals</p>
        <p className="text-[11px] text-muted-foreground">Deal Finder</p>
      </div>
    </div>
  )
}

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r bg-background md:flex">
        <div className="flex h-16 items-center border-b">
          <Brand />
        </div>
        <div className="flex-1 overflow-y-auto p-3">
          <NavLinks />
        </div>
        <div className="flex items-center justify-between border-t p-3">
          <span className="text-[11px] text-muted-foreground">
            Canadian running shoe deals
          </span>
          <ThemeToggle />
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background px-4 md:hidden">
        <Brand />
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen((o) => !o)}
            aria-label="Toggle navigation"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </header>

      {/* Mobile slide-down menu */}
      {mobileOpen && (
        <div className="sticky top-16 z-20 border-b bg-background p-3 md:hidden">
          <NavLinks onNavigate={() => setMobileOpen(false)} />
        </div>
      )}

      {/* Main content */}
      <main className="md:pl-60">
        <div className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
