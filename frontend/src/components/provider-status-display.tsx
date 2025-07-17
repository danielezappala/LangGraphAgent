"use client";

import { useProviderStatus } from "@/hooks/use-provider-status";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Settings, CheckCircle, XCircle, AlertCircle, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

type DisplayMode = 'indicator' | 'alert' | 'full';

interface ProviderStatusDisplayProps {
  mode?: DisplayMode;
  onDismiss?: () => void;
  className?: string;
}

export function ProviderStatusDisplay({ 
  mode = 'indicator', 
  onDismiss,
  className = ""
}: ProviderStatusDisplayProps) {
  const { activeProvider, hasActiveProvider, configurationIssues, isLoading, error } = useProviderStatus();
  const [isDismissed, setIsDismissed] = useState(false);
  const router = useRouter();

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  const getConnectionIcon = () => {
    if (!activeProvider) return <XCircle className="h-4 w-4 text-red-500" />;
    
    switch (activeProvider.connection_status) {
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getProviderTypeLabel = () => {
    if (!activeProvider) return '';
    return activeProvider.provider_type === 'openai' ? 'OpenAI' : 'Azure OpenAI';
  };

  const hasIssues = !hasActiveProvider || configurationIssues.length > 0 || !!error;

  // Alert mode - only show when there are issues and not dismissed
  if (mode === 'alert') {
    if (isLoading || isDismissed || !hasIssues) {
      return null;
    }

    const getAlertMessage = () => {
      if (error) {
        return `Configuration error: ${error}`;
      }
      
      if (!hasActiveProvider) {
        return "No active LLM provider configured. Please set up a provider to use the chatbot.";
      }
      
      if (configurationIssues.length > 0) {
        return `Configuration issues: ${configurationIssues.join(', ')}`;
      }
      
      return "Provider configuration needs attention.";
    };

    return (
      <Alert className={`mb-4 border-orange-200 bg-orange-50 ${className}`}>
        <AlertCircle className="h-4 w-4 text-orange-600" />
        <AlertDescription className="flex items-center justify-between">
          <div className="flex-1">
            <span className="text-orange-800">{getAlertMessage()}</span>
          </div>
          <div className="flex items-center space-x-2 ml-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/settings')}
              className="text-orange-700 border-orange-300 hover:bg-orange-100"
            >
              <Settings className="h-3 w-3 mr-1" />
              Fix Settings
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className="text-orange-600 hover:bg-orange-100"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Indicator mode - always show current status
  if (mode === 'indicator') {
    if (isLoading) {
      return (
        <div className={`flex items-center space-x-2 p-2 bg-gray-50 rounded-lg ${className}`}>
          <div className="animate-pulse h-4 w-4 bg-gray-300 rounded-full"></div>
          <span className="text-sm text-gray-500">Loading provider...</span>
        </div>
      );
    }

    if (!hasActiveProvider || !activeProvider) {
      return (
        <div className={`flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg ${className}`}>
          <div className="flex items-center space-x-2">
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm font-medium text-red-900">No Active Provider</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/settings')}
            className="text-red-700 border-red-300 hover:bg-red-100"
          >
            <Settings className="h-3 w-3 mr-1" />
            Configure
          </Button>
        </div>
      );
    }

    return (
      <div className={`flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg ${className}`}>
        <div className="flex items-center space-x-3">
          {getConnectionIcon()}
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-green-900">
                {activeProvider.name}
              </span>
              <Badge variant="outline" className="text-xs">
                {getProviderTypeLabel()}
              </Badge>
              {activeProvider.is_from_env && (
                <Badge variant="secondary" className="text-xs">
                  Environment
                </Badge>
              )}
            </div>
            <p className="text-xs text-green-700">
              Active AI Provider • {activeProvider.model || 'Default Model'}
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/settings')}
          className="text-green-700 hover:bg-green-100"
        >
          <Settings className="h-3 w-3 mr-1" />
          Manage
        </Button>
      </div>
    );
  }

  // Full mode - comprehensive display with both indicator and alert functionality
  if (mode === 'full') {
    return (
      <div className={`space-y-3 ${className}`}>
        {/* Always show the indicator */}
        <ProviderStatusDisplay mode="indicator" />
        
        {/* Show alert only if there are issues */}
        {hasIssues && !isDismissed && (
          <ProviderStatusDisplay mode="alert" onDismiss={handleDismiss} />
        )}
      </div>
    );
  }

  return null;
}