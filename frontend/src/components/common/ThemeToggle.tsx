import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { Button } from '@/components/ui/button';

export const ThemeToggle: React.FC<{ className?: string }> = ({ className }) => {
  const { theme, setTheme, isDark } = useTheme();

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark');
  };

  return (
    <Button
      variant="outline"
      size="icon-sm"
      onClick={toggleTheme}
      className={className}
      title={`Switch to ${isDark ? 'Light' : 'Dark'} mode (current: ${theme})`}
      aria-label="Toggle theme"
    >
      {isDark ? (
        <Sun className="h-3.5 w-3.5 text-accent transition-transform rotate-0 hover:rotate-45 duration-300" />
      ) : (
        <Moon className="h-3.5 w-3.5 text-accent transition-transform -rotate-12 hover:rotate-0 duration-300" />
      )}
    </Button>
  );
};
