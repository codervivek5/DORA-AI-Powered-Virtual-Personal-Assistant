"use client";

import React from 'react';
import ChatWindow from './ChatWindow';
import AccessibilityTester from './AccessibilityTester';

/**
 * Demo Component - Demonstrates the refactored DORA AI Chat Interface
 * 
 * This component showcases:
 * - Modular component architecture
 * - Accessibility features
 * - Responsive design
 * - Keyboard navigation
 * - Screen reader support
 * 
 * Usage Example:
 * ```jsx
 * import Demo from '@/components/Demo';
 * 
 * function App() {
 *   return <Demo />;
 * }
 * ```
 */
const Demo = () => {
  return (
    <div className="min-h-screen">
      {/* Accessibility announcement for screen readers */}
      <div className="sr-only" aria-live="polite">
        DORA AI Chat Interface loaded. Use Tab to navigate, Enter to send messages, and Escape to clear input.
      </div>
      
      {/* Main chat interface */}
      <ChatWindow />
      
      {/* Accessibility testing tool (development only) */}
      <AccessibilityTester />
    </div>
  );
};

export default Demo;
