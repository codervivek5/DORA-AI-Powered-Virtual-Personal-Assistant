"use client";

import React, { useState, useRef, useEffect } from "react";
import MessageList from "./MessageList";
import UserInput from "./UserInput";
import VoiceToggleButton from "./VoiceToggleButton";
import { motion } from "framer-motion";
/**
 * ChatWindow - Main chat interface component for DORA AI
 *
 * Enhanced Accessibility Features:
 * - Comprehensive ARIA landmarks and labels
 * - Skip navigation links for screen readers
 * - Live region announcements for dynamic content
 * - Keyboard shortcuts and navigation
 * - Focus management and restoration
 * - High contrast mode support
 *
 * Responsive Design:
 * - Mobile-first responsive layout
 * - Flexible grid system with CSS Grid and Flexbox
 * - Adaptive typography and spacing
 * - Touch-optimized interactions
 * - Viewport-aware component sizing
 */

const ChatWindow = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "assistant",
      content:
        "Hello! I'm DORA, your AI-powered virtual personal assistant. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [announceMessage, setAnnounceMessage] = useState("");
  const messagesEndRef = useRef(null);
  const skipLinkRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

    // Announce new messages to screen readers
    if (messages.length > 1) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.type === "assistant") {
        setAnnounceMessage(`DORA responded: ${lastMessage.content}`);
        setTimeout(() => setAnnounceMessage(""), 100);
      }
    }
  }, [messages]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Alt + I to focus input
      if (e.altKey && e.key === "i") {
        e.preventDefault();
        inputRef.current?.focus();
      }
      // Alt + V to toggle voice
      if (e.altKey && e.key === "v") {
        e.preventDefault();
        handleVoiceToggle();
      }
      // Escape to clear focus
      if (e.key === "Escape") {
        document.activeElement?.blur();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isVoiceActive]);

  const handleSendMessage = async (content) => {
    if (!content.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const aiResponse = {
        id: Date.now() + 1,
        type: "assistant",
        content: `I understand you said: "${content.trim()}". This is a simulated response from DORA AI. In a real implementation, this would connect to your AI backend.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceToggle = () => {
    setIsVoiceActive(!isVoiceActive);
    // Voice functionality would be implemented here
  };

  const containerVariants = {
    hidden: { opacity: 0, scale: 0 },
    visible: {
      opacity: 1,
      scale: [0, 1.2, 0.9, 1],
      transition: {
        duration: 0.5,
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
      transition: { duration: 0.4, ease: "easeOut" },
    },
  };

  return (
    <>
      {/* Skip Navigation Links */}
      <div className="sr-only">
        <a
          ref={skipLinkRef}
          href="#main-content"
          className="absolute top-0 left-0 z-50 p-2 bg-primary text-primary-foreground focus:not-sr-only focus:relative"
          onFocus={(e) => e.target.classList.remove("sr-only")}
          onBlur={(e) => e.target.classList.add("sr-only")}
        >
          Skip to main content
        </a>
        <a
          href="#message-input"
          className="absolute top-0 left-0 z-50 p-2 bg-primary text-primary-foreground focus:not-sr-only focus:relative"
          onFocus={(e) => e.target.classList.remove("sr-only")}
          onBlur={(e) => e.target.classList.add("sr-only")}
        >
          Skip to message input
        </a>
      </div>

      {/* Live region for announcements */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        role="status"
      >
        {announceMessage}
      </div>

      {/* Keyboard shortcuts help */}
      <div className="sr-only" aria-label="Keyboard shortcuts">
        Press Alt+I to focus message input, Alt+V to toggle voice, Escape to
        clear focus
      </div>

      <div
        id="main-content"
        className="flex flex-col h-screen max-h-screen glass-chat-container rounded-lg m-4"
        role="main"
        aria-label="DORA AI Chat Interface"
      >
        {/* Top Bar */}
        <header className="flex items-center justify-between p-4 header-glass rounded-t-lg">
          <div className="flex items-center gap-3">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="w-8 h-8 primary-button rounded-lg flex items-center justify-center"
            >
              <motion.span
                variants={childVariants}
                className="text-white font-bold text-sm"
              >
                D
              </motion.span>
            </motion.div>

            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="flex flex-col items-center"
            >
              <motion.h1
                variants={childVariants}
                className="text-lg font-semibold text-high-contrast"
              >
                DORA AI
              </motion.h1>

              <motion.p
                variants={childVariants}
                className="text-sm text-medium-contrast"
              >
                Your AI Assistant
              </motion.p>
            </motion.div>
          </div>
          <div className="flex items-center gap-2">
            <VoiceToggleButton
              isActive={isVoiceActive}
              onToggle={handleVoiceToggle}
            />
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {messages.length <= 1 ? (
            /* Welcome Screen - Only show when no conversation has started */
            <div className="flex-1 flex flex-col items-center justify-center px-4 text-center">
              <div className="max-w-2xl mx-auto space-y-6">
                <motion.div
                  initial={{ opacity: 0, y: 50 }} // starting state
                  animate={{ opacity: 1, y: 0 }} // animate to
                  transition={{ duration: 0.5 }} // animation speed
                  className="space-y-4"
                >
                  <h2 className="text-4xl font-bold text-high-contrast">
                    Introducing DORA AI
                  </h2>
                  <p className="text-lg text-medium-contrast leading-relaxed">
                    Your intelligent virtual personal assistant designed to
                    streamline your daily tasks, manage your schedule, and help
                    you stay organized effortlessly.
                  </p>
                </motion.div>

                {/* Feature highlights */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                  <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="p-4 rounded-lg feature-card"
                  >
                    <motion.div
                      variants={childVariants}
                      className="w-8 h-8 glass-card rounded-lg flex items-center justify-center mb-3"
                    >
                      <span className="text-2xl">🤖</span>
                    </motion.div>

                    <motion.h3
                      variants={childVariants}
                      className="font-semibold text-high-contrast mb-2"
                    >
                      Smart Conversations
                    </motion.h3>

                    <motion.p
                      variants={childVariants}
                      className="text-sm text-medium-contrast"
                    >
                      Natural language processing for intuitive interactions
                    </motion.p>
                  </motion.div>
                  <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="p-4 rounded-lg feature-card"
                  >
                    <motion.div
                      variants={childVariants}
                      className="w-8 h-8 glass-card rounded-lg flex items-center justify-center mb-3"
                    >
                      <span className="text-2xl">📅</span>
                    </motion.div>
                    <motion.h3
                      variants={childVariants}
                      className="font-semibold text-high-contrast mb-2"
                    >
                      Task Management
                    </motion.h3>
                    <motion.p
                      variants={childVariants}
                      className="text-sm text-medium-contrast"
                    >
                      Organize and track your daily tasks efficiently
                    </motion.p>
                  </motion.div>
                  <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="p-4 rounded-lg feature-card"
                  >
                    <motion.div
                      variants={childVariants}
                      className="w-8 h-8 glass-card rounded-lg flex items-center justify-center mb-3"
                    >
                      <span className="text-2xl">🎯</span>
                    </motion.div>
                    <motion.h3
                      variants={childVariants}
                      className="font-semibold text-high-contrast mb-2"
                    >
                      Personalized Help
                    </motion.h3>
                    <motion.p
                      variants={childVariants}
                      className="text-sm text-medium-contrast"
                    >
                      Tailored assistance based on your preferences
                    </motion.p>
                  </motion.div>
                </div>
              </div>
            </div>
          ) : (
            /* Chat Messages Area */
            <div
              className="flex-1 overflow-y-auto p-4 space-y-4 gradient-scrollbar"
              role="log"
              aria-live="polite"
              aria-label="Chat messages"
            >
              <MessageList messages={messages} isLoading={isLoading} />
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Input Area - Always visible at bottom */}
          <div className="header-glass p-4 rounded-b-lg">
            <UserInput
              ref={inputRef}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              isVoiceActive={isVoiceActive}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatWindow;
