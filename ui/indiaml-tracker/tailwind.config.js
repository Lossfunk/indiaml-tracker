/** @type {import('tailwindcss').Config} */
const { fontFamily } = require("tailwindcss/defaultTheme") // Import default theme

module.exports = {
  darkMode: ["class"], // Enable class-based dark mode
  content: [
    "./pages/**/*.{ts,tsx,js,jsx}",
    "./components/**/*.{ts,tsx,js,jsx}", // Make sure this points to your components
    "./app/**/*.{ts,tsx,js,jsx}",
    "./src/**/*.{ts,tsx,js,jsx}", // Include src if applicable
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      // Define colors using HSL variables from globals.css
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
         // Add specific semantic colors if needed, referencing base Tailwind colors
         // or defining custom HSL values (ensure these have dark mode equivalents)
         // Example:
         // usColor: { DEFAULT: '#3b82f6', dark: '#60a5fa' }, // blue-500, blue-400
         // cnColor: { DEFAULT: '#ef4444', dark: '#f87171' }, // red-500, red-400
         // inColor: { DEFAULT: '#f59e0b', dark: '#fbbf24' }, // amber-500, amber-400
      },
      // Define border radius using CSS variable
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      // Keep custom utilities if needed
      boxShadow: {
        nb1: "1px 1px 0px 1px #000000",
      },
       // Add Rubik font, extending the default sans-serif stack
      fontFamily: {
        sans: ["Rubik", ...fontFamily.sans], // Add Rubik before the defaults
      },
      // Keep keyframes if used by other components or Shadcn UI
      keyframes: {
        "accordion-down": {
          from: { height: "0" }, // Use string "0"
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" }, // Use string "0"
        },
         // Add fadeIn if you want to use it via Tailwind class directly
         // "fade-in": {
         //   '0%': { opacity: '0', transform: 'translateY(10px)' },
         //   '100%': { opacity: '1', transform: 'translateY(0)' },
         // },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
         // "fade-in": "fade-in 0.5s ease-out forwards", // Add if needed
      },
       // Keep other extensions if needed
       backgroundImage: {
        'dot-grid': "radial-gradient(circle, #777 1px, transparent 1px)",
       },
       clipPath: {
         'fancy': 'polygon(50% 0, 100% 50%, 50% 100%, 0 50%)',
       },
       backgroundSize: {
         '20': '20px 20px',
         '14': '14px 14px',
       },
    },
  },
  plugins: [
    require("tailwindcss-animate"), // Keep for accordion animations etc.
    require("@tailwindcss/aspect-ratio"), // Keep if using aspect ratio utilities
    // Add clip-path plugin if used
    // require('tailwind-clip-path'),
  ],
};