import { Button } from "@/components/ui/button"
import {Link} from 'react-router-dom'

export function TopNav() {
  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-xl font-bold text-gray-800">
            Indian Research Papers
          </Link>
          <div className="space-x-4">
            <Button variant="ghost" className="text-gray-600 hover:text-gray-800 hover:bg-gray-100" asChild>
              <Link to="/">Home</Link>
            </Button>
            <Button variant="ghost" className="text-gray-600 hover:text-gray-800 hover:bg-gray-100" asChild>
              <Link to="/about">About</Link>
            </Button>
            <Button variant="ghost" className="text-gray-600 hover:text-gray-800 hover:bg-gray-100" asChild>
              <Link to="/motivation">Motivation</Link>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}

