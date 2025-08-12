import React from 'react';
import { cn } from '@/lib/utils';

/**
 * LoadingIndicator component for showing typing/loading states
 * 
 * Accessibility Features:
 * - ARIA live region for status updates
 * - Screen reader announcements
 * - Proper loading state semantics
 * - Non-intrusive visual feedback
 * 
 * Responsive Design:
 * - Responsive sizing and spacing
 * - Mobile-optimized layout
 * - Smooth animations
 */
const LoadingIndicator = () => {
  return (
    <div 
      className="flex justify-start"
      role="status"
      aria-live="polite"
      aria-label="DORA is typing"
    >
      <div 
        className={cn(
          "max-w-[80%] sm:max-w-[70%] md:max-w-[60%] lg:max-w-[50%]",
          "rounded-2xl px-4 py-3",
          "message-bubble-assistant"
        )}
      >
        <div className="flex items-center gap-2">
          {/* Animated dots */}
          <div className="flex gap-1">
            <div 
              className="w-2 h-2 loading-dots rounded-full animate-bounce"
              style={{ animationDelay: '0ms' }}
              aria-hidden="true"
            />
            <div 
              className="w-2 h-2 loading-dots rounded-full animate-bounce"
              style={{ animationDelay: '150ms' }}
              aria-hidden="true"
            />
            <div 
              className="w-2 h-2 loading-dots rounded-full animate-bounce"
              style={{ animationDelay: '300ms' }}
              aria-hidden="true"
            />
          </div>
          
          {/* Text for screen readers */}
          <span className="sr-only">
            DORA is typing a response...
          </span>
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;
