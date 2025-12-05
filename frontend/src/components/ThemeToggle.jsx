"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { useTheme } from './ThemeProvider';
import { Sun, Moon } from 'lucide-react';

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();

  const handleClick = () => {
    toggleTheme();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <button
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={cn(
        "flex items-center justify-center",
        "w-10 h-10 rounded-lg border border-input",
        "bg-background hover:bg-accent hover:text-accent-foreground",
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        "transition-all duration-200",
        "touch-manipulation"
      )}
      aria-label={theme === 'dark' ? "Switch to light mode" : "Switch to dark mode"}
      aria-describedby="theme-toggle-description"
      tabIndex={0}
      role="button"
      type="button"
    >
      {theme === 'dark' ? (
        <Sun className="w-5 h-5" aria-hidden="true" />
      ) : (
        <Moon className="w-5 h-5" aria-hidden="true" />
      )}
      <span id="theme-toggle-description" className="sr-only">
        {theme === 'dark' 
          ? "Currently in dark mode. Click to switch to light mode." 
          : "Currently in light mode. Click to switch to dark mode."
        }
      </span>
    </button>
  );
};

export default ThemeToggle;
