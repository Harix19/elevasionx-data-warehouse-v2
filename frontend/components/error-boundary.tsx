'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCcw } from 'lucide-react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center bg-card rounded-xl border border-border shadow-sm">
          <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mb-6">
            <AlertCircle className="w-8 h-8 text-destructive" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground mb-2">Something went wrong</h2>
          <p className="text-muted-foreground mb-8 max-w-md mx-auto">
            An unexpected error occurred while rendering this component. Our team has been notified.
          </p>
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={this.handleReset} className="gap-2">
              <RefreshCcw className="w-4 h-4" />
              Try again
            </Button>
            <Button asChild>
              <a href="/">Go to Homepage</a>
            </Button>
          </div>
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <div className="mt-8 p-4 bg-muted rounded-lg text-left overflow-auto max-w-full">
              <p className="text-xs font-mono text-muted-foreground break-all">
                {this.state.error.toString()}
              </p>
            </div>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
