"use client";

import { useProviderStatus } from "@/hooks/use-provider-status";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Settings, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";

export function ProviderStatusIndicator() {
  const { activeProvider, hasActiveProvider, isLoading } = useProviderStatus();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
        <div className="animate-pulse h-4 w-4 bg-gray-300 rounded-full"></div>
        <span className="text-sm text-gray-500">Loading provider...</span>
      </div>
    );
  }

  if (!hasActiveProvider || !activeProvider) {
    return (
      <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
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

  const getConnectionIcon = () => {
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
    return activeProvider.provider_type === 'openai' ? 'OpenAI' : 'Azure OpenAI';
  };

  return (
    <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
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