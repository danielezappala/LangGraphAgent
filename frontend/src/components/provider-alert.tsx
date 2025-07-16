"use client";

import { useProviderStatus } from "@/hooks/use-provider-status";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, Settings, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface ProviderAlertProps {
  onDismiss?: () => void;
}

export function ProviderAlert({ onDismiss }: ProviderAlertProps) {
  const { hasActiveProvider, configurationIssues, isLoading, error } = useProviderStatus();
  const [isDismissed, setIsDismissed] = useState(false);
  const router = useRouter();

  // Don't show alert if loading or dismissed
  if (isLoading || isDismissed) {
    return null;
  }

  // Don't show alert if everything is properly configured
  if (hasActiveProvider && configurationIssues.length === 0 && !error) {
    return null;
  }

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

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
    <Alert className="mb-4 border-orange-200 bg-orange-50">
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