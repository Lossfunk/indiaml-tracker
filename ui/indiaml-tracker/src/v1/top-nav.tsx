import { Button } from "@/components/ui/button"
import {Link} from 'react-router-dom'
import AnimatedLogo from "./animated-logo"

export function TopNav() {
  return (
    <nav className="border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/papers" className="text-xl font-bold">
          <div className="h-16 flex items-center">
          <div className="h-full">
          <AnimatedLogo/>
          </div>

          <div>
            India@ML
          </div>
          </div>
            {/* India@ML */}
          </Link>
          <div className="space-x-4">
            <Button variant="ghost" className="text-gray-200 hover:text-gray-800 hover:bg-gray-100" asChild>
              <Link to="/motivation">Motivation</Link>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}

