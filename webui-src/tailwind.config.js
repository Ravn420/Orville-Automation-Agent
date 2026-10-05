/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#ffffff',
        foreground: '#231d17',
        card: '#ffffff',
        'card-foreground': '#231d17',
        popover: '#ffffff',
        'popover-foreground': '#231d17',
        secondary: '#f8f8f9',
        'secondary-foreground': '#4e463f',
        muted: '#f4f4f5',
        'muted-foreground': '#71717b',
        accent: '#f4f4f5',
        'accent-foreground': '#09090b',
        destructive: '#e7000b',
        'destructive-foreground': '#ffffff',
        border: '#e4e4e7',
        input: '#e4e4e7',
        ring: '#2b7fff',
        sidebar: '#fafafa',
        'sidebar-foreground': '#231d17',
        'sidebar-primary': '#0057c0',
        'sidebar-primary-foreground': '#ffffff',
        'sidebar-accent': '#f4f4f5',
        'sidebar-accent-foreground': '#09090b',
        'sidebar-border': '#e4e4e7',
        'sidebar-ring': '#2b7fff',
        // NOVA design tokens
        nova: {
          primary: '#0057c0',
          'primary-hover': '#004494',
          'primary-pressed': '#00336e',
          'primary-disabled': '#9dbfe0',
        }
      },
      borderRadius: {
        lg: '0.65rem',
        md: 'calc(0.65rem - 2px)',
        sm: 'calc(0.65rem - 4px)',
      },
      fontFamily: {
        sans: ['Segoe UI', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}