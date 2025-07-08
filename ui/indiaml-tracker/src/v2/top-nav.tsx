"use client";

import { useState } from "react";
import { Link } from "react-router-dom"; // Assuming you're using React Router
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Moon, Sun, Menu } from "lucide-react";
import AnimatedLogo from "./animated-logo";

export function TopNav() {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);

  return (
    <nav className="border-b border-gray-200 bg-white dark:bg-gray-900">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/papers" className="text-xl font-bold">
            <div className="h-16 flex items-center">
              <div className="h-full">
                <AnimatedLogo />
              </div>

              <div>India@ML</div>
            </div>
            {/* India@ML */}
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex space-x-2">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              aria-label="Toggle theme"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>

            <Button
              variant="ghost"
              className="text-gray-900 dark:text-gray-200 hover:text-gray-800"
              asChild
            >
              {/* <Link to="/motivation">Our Motivation</Link> */}
              <Link to="/conference-summary?conference=ICLR&year=2025">
                Conference Summaries
              </Link>
            </Button>

            {/* Motivation Link */}
            <Button
              variant="ghost"
              className="text-gray-900 dark:text-gray-200 hover:text-gray-800"
              asChild
            >
              <Link to="/motivation">Our Motivation</Link>
              </Button>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Menu className="h-6 w-6" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-64">
                <div className="pt-4 px-2 space-y-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="w-full flex justify-start pl-3"
                    onClick={() => {
                      setTheme(theme === "dark" ? "light" : "dark");
                      setOpen(false);
                    }}
                  >
                    <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                    <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                    <span className="ml-2">Toggle Theme</span>
                  </Button>

                  <Button
                    variant="ghost"
                    className="w-full flex justify-start"
                    asChild
                  >
                    <Link to="/motivation" onClick={() => setOpen(false)}>
                      Motivation
                    </Link>
                  </Button>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </nav>
  );
}
