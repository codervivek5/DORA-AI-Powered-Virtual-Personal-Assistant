"use client";

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { runAccessibilityTests, logAccessibilityResults } from '@/utils/accessibility';
import { CheckCircle, XCircle, AlertTriangle, Play, Eye, EyeOff } from 'lucide-react';

/**
 * AccessibilityTester - Development tool for testing accessibility features
 * 
 * This component provides a visual interface for running accessibility tests
 * and viewing results during development. It should only be used in development mode.
 */
const AccessibilityTester = () => {
  const [testResults, setTestResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [lastRunTime, setLastRunTime] = useState(null);

  useEffect(() => {
    // Auto-run tests on component mount
    runTests();
  }, []);

  const runTests = async () => {
    setIsRunning(true);
    try {
      const results = await runAccessibilityTests();
      setTestResults(results);
      setLastRunTime(new Date());
      
      // Also log to console
      await logAccessibilityResults();
    } catch (error) {
      console.error('Failed to run accessibility tests:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const toggleVisibility = () => {
    setIsVisible(!isVisible);
  };

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={toggleVisibility}
        className={cn(
          "fixed bottom-4 right-4 z-50",
          "w-12 h-12 rounded-full",
          "primary-button",
          "shadow-lg hover:shadow-xl",
          "transition-all duration-200",
          "focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2"
        )}
        aria-label={isVisible ? "Hide accessibility tester" : "Show accessibility tester"}
        title="Accessibility Tester"
      >
        {isVisible ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
      </button>

      {/* Test Results Panel */}
      {isVisible && (
        <div
          className={cn(
            "fixed bottom-20 right-4 z-40",
            "w-80 max-h-96 overflow-y-auto gradient-scrollbar",
            "accessibility-panel rounded-lg shadow-xl",
            "p-4 space-y-4"
          )}
          role="dialog"
          aria-label="Accessibility Test Results"
        >
          {/* Header */}
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-high-contrast">
              Accessibility Tests
            </h3>
            <button
              onClick={runTests}
              disabled={isRunning}
              className={cn(
                "flex items-center gap-2 px-3 py-1",
                "primary-button rounded-md",
                "disabled:opacity-50",
                "transition-colors duration-200",
                "focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2"
              )}
              aria-label="Run accessibility tests"
            >
              <Play className="w-4 h-4" />
              {isRunning ? 'Running...' : 'Run Tests'}
            </button>
          </div>

          {/* Last Run Time */}
          {lastRunTime && (
            <div className="text-xs text-muted-foreground">
              Last run: {lastRunTime.toLocaleTimeString()}
            </div>
          )}

          {/* Test Results */}
          {testResults && (
            <div className="space-y-3">
              {/* Summary */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="flex flex-col items-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
                  <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                  <span className="text-sm font-medium text-green-700 dark:text-green-300">
                    {testResults.passed.length}
                  </span>
                  <span className="text-xs text-green-600 dark:text-green-400">
                    Passed
                  </span>
                </div>
                
                <div className="flex flex-col items-center p-2 bg-red-50 dark:bg-red-900/20 rounded">
                  <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                  <span className="text-sm font-medium text-red-700 dark:text-red-300">
                    {testResults.failed.length}
                  </span>
                  <span className="text-xs text-red-600 dark:text-red-400">
                    Failed
                  </span>
                </div>
                
                <div className="flex flex-col items-center p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                  <span className="text-sm font-medium text-yellow-700 dark:text-yellow-300">
                    {testResults.warnings.length}
                  </span>
                  <span className="text-xs text-yellow-600 dark:text-yellow-400">
                    Warnings
                  </span>
                </div>
              </div>

              {/* Axe Results Summary */}
              {testResults.axeResults && (
                <div className="p-3 bg-muted rounded-lg">
                  <h4 className="text-sm font-medium mb-2">Axe-Core Results</h4>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span>Violations:</span>
                      <span className={testResults.axeResults.violations.length === 0 ? 'text-green-600' : 'text-red-600'}>
                        {testResults.axeResults.violations.length}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Passes:</span>
                      <span className="text-green-600">{testResults.axeResults.passes.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Incomplete:</span>
                      <span className="text-yellow-600">{testResults.axeResults.incomplete.length}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Quick Tips */}
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <h4 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">
                  Quick Tips
                </h4>
                <ul className="text-xs text-blue-600 dark:text-blue-400 space-y-1">
                  <li>• Use Tab to navigate between elements</li>
                  <li>• Press Alt+I to focus message input</li>
                  <li>• Press Alt+V to toggle voice input</li>
                  <li>• Press Ctrl+C on messages to copy</li>
                  <li>• Check console for detailed results</li>
                </ul>
              </div>
            </div>
          )}

          {/* Loading State */}
          {isRunning && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default AccessibilityTester;