import { Button } from "@/components/ui/button"
import {Link} from 'react-router-dom'
import AnimatedLogo from "./animated-logo"
import { useTheme } from "@/components/theme-provider"
import { Sun, Moon, Monitor } from "lucide-react"

export function TopNav() {
  const { theme, setTheme } = useTheme()

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
          <div className="space-x-4 flex items-center">
            <Button variant="ghost" className="text-gray-200 hover:text-gray-800 hover:bg-gray-100" asChild>
              <Link to="/motivation">Motivation</Link>
            </Button>
            <div className="flex items-center space-x-2">
              <Button variant="ghost" onClick={() => setTheme("light")}>
                <Sun className="w-5 h-5" />
              </Button>
              <Button variant="ghost" onClick={() => setTheme("dark")}>
                <Moon className="w-5 h-5" />
              </Button>
              <Button variant="ghost" onClick={() => setTheme("system")}>
                <Monitor className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
