'use client';
import React from 'react';
import ChatWindow from '@/components/ChatWindow';

/**
 * Main HomePage component that renders the DORA AI chat interface
 * 
 * This component serves as the entry point for the chat application
 * and provides the main layout structure.
 */
const HomePage = () => {
  
  return (
    <div className="h-screen w-full">
      
      <ChatWindow />
    </div>
  );
};

export default HomePage;
