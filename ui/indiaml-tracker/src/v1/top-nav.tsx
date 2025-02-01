import { Button } from "@/components/ui/button"
import {Link} from 'react-router-dom'

export function TopNav() {
  return (
    <nav className="border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/papers-2024" className="text-xl font-bold">
            India@ML
          </Link>
          <div className="space-x-4">
            <Button variant="ghost" className="text-gray-200 hover:text-gray-800 hover:bg-gray-100" asChild>
              <Link to="/">Home</Link>
            </Button>
            <Button variant="ghost" className="text-gray-200 hover:text-gray-800 hover:bg-gray-100" asChild>
              <Link to="/about">About</Link>
            </Button>
            <Button variant="ghost" className="text-gray-200 hover:text-gray-800 hover:bg-gray-100" asChild>
              <Link to="/motivation">Motivation</Link>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}

