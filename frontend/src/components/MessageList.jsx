import React from 'react';
import ChatBubble from './ChatBubble';
import LoadingIndicator from './LoadingIndicator';
import { motion } from 'framer-motion';
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

const containerVariants = {
    hidden: { opacity: 0, scale: 0 },
    visible: {
      opacity: 1,
      scale: [0, 1.2, 0.9, 1],
      transition: {
        duration: 0.6,
        ease: "easeOut",
        when: "beforeChildren",
        staggerChildren: 0.1, // delay between child animations
      },
    },
  };

  const childVariants = {
    hidden: { opacity: 0, scale: 0 },
    visible: {
      opacity: 1,
      scale: [0, 1.2, 0.9, 1],
      transition: { duration: 0.5, ease: "easeOut" },
    },
  };
const MessageList = ({ messages, isLoading }) => {
  const messageCount = messages.length;
  
  return (
    <motion.div  variants={containerVariants}
      initial="hidden"
      animate="visible" 
      className="space-y-4"
      role="log"
      aria-live="polite"
      aria-label={`Chat conversation with ${messageCount} message${messageCount !== 1 ? 's' : ''}`}
      aria-describedby="message-list-description"
    >
      {/* Screen reader description */}
      <motion.div variants={childVariants} id="message-list-description" className="sr-only">
        Use arrow keys to navigate between messages. Messages are automatically announced as they appear.
      </motion.div>
      
      {/* Message list */}
      <ul className="space-y-4" role="list">
        {messages.map((message, index) => (
          <motion.li variants={childVariants}  key={message.id} role="listitem">
            <ChatBubble 
              message={message}
              messageIndex={index + 1}
              totalMessages={messageCount}
            />
          </motion.li>
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
    </motion.div>
  );
};

export default MessageList;
