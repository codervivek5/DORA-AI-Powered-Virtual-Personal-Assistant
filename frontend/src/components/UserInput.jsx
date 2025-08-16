"use client";

import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Send, Mic, MicOff, Plus } from 'lucide-react';
import {motion} from 'framer-motion';
const UserInput = React.forwardRef(({ onSendMessage, isLoading, isVoiceActive }, ref) => {
  const [inputValue, setInputValue] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const inputRef = useRef(null);
  const sendButtonRef = useRef(null);

  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus();
    }
  }, [isLoading]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (canSend) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (canSend) {
        onSendMessage(inputValue);
        setInputValue('');
      }
    } else if (e.key === 'Escape') {
      setInputValue('');
      inputRef.current?.blur();
    }
  };

  const handleCompositionStart = () => {
    setIsComposing(true);
  };

  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  const handleVoiceToggle = () => {
    // Voice toggle functionality
    console.log('Voice toggle clicked');
  };

  const handleAttachment = () => {
    // Attachment functionality
    console.log('Attachment clicked');
  };

  const canSend = inputValue.trim() && !isLoading && !isComposing;

  return (
    <motion.div initial={{ opacity: 0, y: -50 }} // starting state
                  animate={{ opacity: 1, y: 0 }} // animate to
                  transition={{ duration: 0.3 }} // animation speed
                   className="max-w-4xl mx-auto">
      <form
        onSubmit={handleSubmit}
        className="relative"
        role="form"
        aria-label="Message input form"
      >
        {/* Main Input Container */}
        <div className={cn(
          "relative flex items-end gap-3",
          "w-full min-h-[52px] max-h-[200px]",
          "input-container rounded-xl",
          "transition-all duration-200",
          "focus-within:ring-2 focus-within:ring-blue-400 focus-within:ring-offset-2",
          "hover:shadow-lg"
        )}>
          {/* Attachment Button */}
          <button
            type="button"
            onClick={handleAttachment}
            disabled={isLoading}
            className={cn(
              "flex items-center justify-center",
              "w-8 h-8 rounded-full",
              "interactive-element",
              "ml-3 mb-2"
            )}
            aria-label="Attach file"
            tabIndex={0}
          >
            <Plus className="w-4 h-4" aria-hidden="true" />
          </button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <textarea
              id="message-input"
              ref={(node) => {
                inputRef.current = node;
                if (ref) {
                  if (typeof ref === 'function') ref(node);
                  else ref.current = node;
                }
              }}
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onCompositionStart={handleCompositionStart}
              onCompositionEnd={handleCompositionEnd}
              placeholder="Ask anything..."
              disabled={isLoading}
              rows={1}
              className={cn(
                "w-full min-h-[44px] max-h-[200px]",
                "bg-transparent border-none outline-none",
                "resize-none",
                "text-high-contrast placeholder-enhanced",
                "text-sm leading-relaxed",
                "py-3 pr-4",
                "focus:ring-0 focus:outline-none"
              )}
              role="textbox"
              aria-label="Message input"
              aria-describedby="input-instructions"
              aria-multiline="true"
              aria-required="true"
              aria-invalid={false}
              tabIndex={0}
            />
            <div id="input-instructions" className="sr-only" aria-live="polite">
              {canSend ? "Press Enter to send message, or Escape to clear input" : "Type a message to enable sending"}
            </div>
          </div>

          {/* Voice Button */}
          <button
            type="button"
            onClick={handleVoiceToggle}
            disabled={isLoading}
            className={cn(
              "flex items-center justify-center",
              "w-8 h-8 rounded-full",
              "interactive-element",
              "mr-2 mb-2"
            )}
            aria-label={isVoiceActive ? "Stop voice input" : "Start voice input"}
            aria-pressed={isVoiceActive}
            tabIndex={0}
          >
            {isVoiceActive ? (
              <MicOff className="w-4 h-4" aria-hidden="true" />
            ) : (
              <Mic className="w-4 h-4" aria-hidden="true" />
            )}
          </button>

          {/* Send Button */}
          <button
            ref={sendButtonRef}
            type="submit"
            disabled={!canSend}
            className={cn(
              "flex items-center justify-center",
              "w-8 h-8 rounded-full",
              "transition-all duration-200",
              "mr-3 mb-2",
              canSend
                ? "primary-button"
                : "button-disabled"
            )}
            aria-label="Send message"
            aria-describedby={!canSend ? "send-disabled-reason" : undefined}
            tabIndex={canSend ? 0 : -1}
          >
            <Send className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        {/* Hidden elements for accessibility */}
        {!canSend && (
          <div id="send-disabled-reason" className="sr-only">
            Send button is disabled. Type a message to enable sending.
          </div>
        )}
        {isLoading && (
          <div className="sr-only" aria-live="polite">
            DORA is typing a response...
          </div>
        )}
      </form>
    </motion.div>
  );
});

UserInput.displayName = 'UserInput';

export default UserInput;
