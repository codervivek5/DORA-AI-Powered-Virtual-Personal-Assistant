"use client";

import React from 'react';
import { cn } from '@/lib/utils';

/**
 * ChatBubble component for rendering individual chat messages
 * 
 * Enhanced Accessibility Features:
 * - Proper ARIA labels for message types
 * - Semantic markup for message content
 * - Screen reader friendly timestamps
 * - Focus indicators for interactive elements
 * - Message position context for screen readers
 * - Copy-to-clipboard functionality
 * 
 * Responsive Design:
 * - Flexible width based on content
 * - Responsive typography and spacing
 * - Mobile-optimized bubble layout
 * - High contrast mode support
 */
const ChatBubble = ({ message, messageIndex = 1, totalMessages = 1 }) => {
  const isUser = message.type === 'user';

  const formatTime = (timestamp) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(timestamp);
  };

  const formattedTime = formatTime(message.timestamp);

  const handleCopyMessage = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      // Could add a toast notification here
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'c' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleCopyMessage();
    }
  };

  return (
    <div
      className={cn(
        "flex w-full py-4",
        isUser ? "justify-end" : "justify-start"
      )}
      aria-label={`Message ${messageIndex} of ${totalMessages} from ${isUser ? 'you' : 'DORA'}`}
    >
      <div
        className={cn(
          "max-w-[85%] sm:max-w-[75%] md:max-w-[65%] lg:max-w-[55%]",
          "rounded-2xl px-4 py-3",
          "transition-all duration-200",
          "focus-within:ring-2 focus-within:ring-blue-400 focus-within:ring-offset-2",
          "hover:shadow-lg hover:transform hover:scale-[1.02]",
          "group cursor-pointer",
          isUser
            ? "message-bubble-user ml-4"
            : "message-bubble-assistant mr-4"
        )}
        tabIndex={0}
        role="article"
        aria-describedby={`message-time-${message.id} message-actions-${message.id}`}
        aria-label={`${isUser ? 'Your' : 'DORA\'s'} message: ${message.content.substring(0, 50)}${message.content.length > 50 ? '...' : ''}`}
        onKeyDown={handleKeyDown}
        onClick={handleCopyMessage}
        title="Click to copy message (Ctrl+C)"
      >
        <div className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>
        <div className="flex items-center justify-between mt-2">
          <div
            id={`message-time-${message.id}`}
            className={cn(
              "text-xs opacity-70",
              isUser ? "text-white/70" : "text-white/70"
            )}
            aria-label={`Message sent at ${formattedTime}`}
          >
            {formattedTime}
          </div>

          {/* Copy indicator */}
          <div
            id={`message-actions-${message.id}`}
            className={cn(
              "text-xs opacity-0 group-hover:opacity-70 transition-opacity",
              isUser ? "text-white/70" : "text-white/70"
            )}
            aria-hidden="true"
          >
            Click to copy
          </div>
        </div>

        <span className="sr-only">
          {isUser ? 'Your message' : 'DORA assistant message'}. Press Ctrl+C to copy this message.
        </span>
      </div>
    </div>
  );
};

export default ChatBubble;
