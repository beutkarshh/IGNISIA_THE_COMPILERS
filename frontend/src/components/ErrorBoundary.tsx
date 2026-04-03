/**
 * Error Boundary Component
 * 
 * Catches JavaScript errors in the component tree and displays a fallback UI.
 */

"use client";
import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import Link from 'next/link';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: string;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: error.stack
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // You could also log the error to an error reporting service here
    // logErrorToService(error, errorInfo);
  }

  handleRetry = () => {
    // Reset the error state to retry rendering
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-6">
          <div className="max-w-md w-full text-center">
            <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="text-red-600 dark:text-red-400" size={32} />
            </div>
            
            <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 mb-2">
              Something went wrong
            </h1>
            
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              An unexpected error occurred while rendering this page. This has been logged for our team to investigate.
            </p>

            <div className="space-y-3">
              <button
                onClick={this.handleRetry}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 transition-colors font-medium"
              >
                <RefreshCw size={16} />
                Try Again
              </button>
              
              <Link
                href="/"
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-2xl hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors font-medium"
              >
                <Home size={16} />
                Go Home
              </Link>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300">
                  Technical Details (Development)
                </summary>
                <div className="mt-3 p-4 bg-slate-100 dark:bg-slate-900 rounded-xl text-xs font-mono text-red-600 dark:text-red-400 overflow-auto max-h-32">
                  <div className="font-bold mb-2">{this.state.error.name}: {this.state.error.message}</div>
                  {this.state.errorInfo && (
                    <pre className="whitespace-pre-wrap">{this.state.errorInfo}</pre>
                  )}
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component to wrap any component with error boundary
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
) {
  const ComponentWithErrorBoundary = (props: P) => (
    <ErrorBoundary fallback={fallback}>
      <WrappedComponent {...props} />
    </ErrorBoundary>
  );

  ComponentWithErrorBoundary.displayName = `withErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;

  return ComponentWithErrorBoundary;
}

/**
 * Simple loading fallback component
 */
export function LoadingFallback({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="flex items-center gap-3">
        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <span className="text-slate-600 dark:text-slate-400 font-medium">{message}</span>
      </div>
    </div>
  );
}

/**
 * Simple error fallback component
 */
export function ErrorFallback({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <AlertTriangle className="text-red-500 mx-auto mb-3" size={24} />
        <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2">Error</h3>
        <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-medium text-sm"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}