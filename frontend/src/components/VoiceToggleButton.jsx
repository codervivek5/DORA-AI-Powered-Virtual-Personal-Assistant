"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { Mic, MicOff } from 'lucide-react';

/**
 * VoiceToggleButton component for toggling voice input functionality
 * 
 * Accessibility Features:
 * - ARIA labels and descriptions
 * - Proper button states (pressed/unpressed)
 * - Keyboard navigation support
 * - Screen reader announcements
 * - Focus indicators
 * 
 * Responsive Design:
 * - Touch-friendly button size
 * - Responsive icon sizing
 * - Mobile-optimized interactions
 */
const VoiceToggleButton = ({ isActive, onToggle }) => {
  const handleClick = () => {
    onToggle();
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
        "w-10 h-10 rounded-lg",
        "focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2",
        "transition-all duration-200",
        "touch-manipulation", // Optimize for touch devices
        isActive 
          ? "primary-button"
          : "interactive-element"
      )}
      aria-label={isActive ? "Disable voice input" : "Enable voice input"}
      aria-pressed={isActive}
      aria-describedby="voice-button-description"
      tabIndex={0}
      role="button"
      type="button"
    >
      {isActive ? (
        <MicOff 
          className="w-5 h-5" 
          aria-hidden="true"
        />
      ) : (
        <Mic 
          className="w-5 h-5" 
          aria-hidden="true"
        />
      )}
      
      {/* Screen reader description */}
      <span id="voice-button-description" className="sr-only">
        {isActive 
          ? "Voice input is currently active. Click to disable voice input."
          : "Voice input is currently disabled. Click to enable voice input."
        }
      </span>
    </button>
  );
};

export default VoiceToggleButton;
