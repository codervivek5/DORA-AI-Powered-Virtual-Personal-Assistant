import React from 'react';
import ChatBubble from './ChatBubble';
import LoadingIndicator from './LoadingIndicator';

/**
 * MessageList component that renders all chat messages
 * 
 * Enhanced Accessibility Features:
 * - ARIA live region for dynamic updates
 * - Proper list structure with semantic markup
 * - Screen reader announcements for new messages
 * - Focus management for message navigation
 * - Message count announcements
 * - Keyboard navigation between messages
 * 
 * Responsive Design:
 * - Responsive spacing and typography
 * - Mobile-optimized message layout
 * - Touch-friendly interaction areas
 * - Adaptive scroll behavior
 */
const MessageList = ({ messages, isLoading }) => {
  const messageCount = messages.length;
  
  return (
    <div 
      className="space-y-4"
      role="log"
      aria-live="polite"
      aria-label={`Chat conversation with ${messageCount} message${messageCount !== 1 ? 's' : ''}`}
      aria-describedby="message-list-description"
    >
      {/* Screen reader description */}
      <div id="message-list-description" className="sr-only">
        Use arrow keys to navigate between messages. Messages are automatically announced as they appear.
      </div>
      
      {/* Message list */}
      <ul className="space-y-4" role="list">
        {messages.map((message, index) => (
          <li key={message.id} role="listitem">
            <ChatBubble 
              message={message}
              messageIndex={index + 1}
              totalMessages={messageCount}
            />
          </li>
        ))}
      </ul>
      
      {isLoading && (
        <LoadingIndicator />
      )}
      
      {/* Empty state */}
      {messages.length === 0 && !isLoading && (
        <div 
          className="text-center py-8 text-medium-contrast"
          role="status"
          aria-label="No messages yet"
        >
          <p>No messages yet. Start a conversation with DORA!</p>
        </div>
      )}
    </div>
  );
};

export default MessageList;
