"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { useProviderStatus, ProviderConfig } from "@/hooks/use-provider-status";
import { Loader2, CheckCircle, XCircle, AlertCircle } from "lucide-react";

type ProviderType = "openai" | "azure";

interface FormConfig {
  id?: number;
  name: string;
  provider: ProviderType;
  apiKey: string;
  model?: string;
  endpoint?: string;
  deployment?: string;
  apiVersion?: string;
  isActive?: boolean;
}

interface LLMProviderSettingsProps {
  onProviderUpdate?: (provider: string) => void;
}

export function LLMProviderSettings({ onProviderUpdate }: LLMProviderSettingsProps = {}) {
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [config, setConfig] = useState<FormConfig>({
    name: "",
    provider: "openai",
    apiKey: "",
    model: "",
    endpoint: "",
    deployment: "",
    apiVersion: "",
    isActive: false
  });
  
  const { toast } = useToast();
  const router = useRouter();
  
  // Use the new provider status hook
  const {
    allProviders,
    activeProvider,
    isLoading,
    error,
    hasActiveProvider,
    configurationIssues,
    refreshStatus,
    testProviderConnection,
    deleteProvider,
    activateProvider
  } = useProviderStatus();

  // Set initial selected provider when data loads
  useEffect(() => {
    if (activeProvider && !selectedProvider) {
      setSelectedProvider(activeProvider.id.toString());
      setConfig({
        id: activeProvider.id,
        name: activeProvider.name,
        provider: activeProvider.provider_type,
        apiKey: activeProvider.api_key,
        model: activeProvider.model || "",
        endpoint: activeProvider.endpoint || "",
        deployment: activeProvider.deployment || "",
        apiVersion: activeProvider.api_version || "",
        isActive: activeProvider.is_active
      });
    }
  }, [activeProvider, selectedProvider]);

  const handleProviderSelect = (id: string) => {
    setSelectedProvider(id);
    
    if (id === "new") {
      // Reset to default new provider form
      setConfig({
        name: "",
        provider: "openai",
        apiKey: "",
        model: "gpt-4",
        endpoint: "",
        deployment: "",
        apiVersion: "2023-05-15",
        isActive: false
      });
    } else {
      // Load the selected provider's data
      const provider = allProviders.find(p => p.id?.toString() === id);
      if (provider) {
        setConfig({
          id: provider.id,
          name: provider.name,
          provider: provider.provider_type,
          apiKey: provider.api_key,
          model: provider.model || "",
          endpoint: provider.endpoint || "",
          deployment: provider.deployment || "",
          apiVersion: provider.api_version || "",
          isActive: provider.is_active
        });
      }
    }
  };
  
  const handleProviderTypeChange = (providerType: ProviderType) => {
    setConfig(prev => {
      const newConfig = {
        ...prev,
        provider: providerType,
        // Reset fields when switching provider types
        endpoint: providerType === "azure" ? prev.endpoint : "",
        deployment: providerType === "azure" ? prev.deployment : "",
        apiVersion: providerType === "azure" ? prev.apiVersion : "",
      };
      
      // Clear model if switching provider types
      if (prev.provider !== providerType) {
        newConfig.model = "";
      }
      
      return newConfig;
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setConfig(prev => {
      const newConfig = {
        ...prev,
        [name]: value,
      };
      
      // If model is changed, clear any provider-specific fields that might be dependent on it
      if (name === 'model') {
        // Add any model-specific logic here if needed
      }
      
      return newConfig;
    });
  };

  interface RequestBody {
    provider: ProviderType;
    api_key?: string;
    model?: string;
    endpoint?: string;
    deployment?: string;
    api_version?: string;
  }

  const handleDeleteProvider = async () => {
    if (!confirm('Are you sure you want to delete this provider? This action cannot be undone.')) {
      return;
    }

    if (!selectedProvider || selectedProvider === 'new') {
      return;
    }

    try {
      setIsSaving(true);
      const success = await deleteProvider(parseInt(selectedProvider));
      
      if (success) {
        // Reset the form to default values
        setSelectedProvider('new');
        setConfig({
          name: '',
          provider: 'openai',
          apiKey: '',
          model: '',
          endpoint: '',
          deployment: '',
          apiVersion: '',
          isActive: false
        });

        toast({
          title: 'Success',
          description: 'Provider deleted successfully',
        });
      } else {
        throw new Error('Failed to delete provider');
      }
    } catch (error) {
      console.error('Error deleting provider:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete provider',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!config.name) {
      toast({
        title: "Error",
        description: "Provider name is required",
        variant: "destructive",
      });
      return;
    }
    
    if (!config.apiKey) {
      toast({
        title: "Error",
        description: "API Key is required",
        variant: "destructive",
      });
      return;
    }
    
    if (config.provider === 'azure' && !config.endpoint) {
      toast({
        title: "Error",
        description: "Endpoint is required for Azure OpenAI",
        variant: "destructive",
      });
      return;
    }
    
    setIsSaving(true);

    try {
      const requestBody: any = {
        name: config.name,
        provider_type: config.provider,
        api_key: config.apiKey,
        model: config.model,
        is_active: true,
        // Azure-specific fields
        ...(config.provider === 'azure' && {
          endpoint: config.endpoint,
          deployment: config.deployment,
          api_version: config.apiVersion
        })
      };

      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '';
      const endpoint = selectedProvider === 'new' 
        ? `${baseUrl}/api/providers/add` 
        : `${baseUrl}/api/providers/switch/${selectedProvider}`;
        
      const method = 'POST';

      const response = await fetch(endpoint, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        const successMessage = selectedProvider === 'new'
          ? `Added new ${config.provider.toUpperCase()} provider`
          : `Updated ${config.provider.toUpperCase()} provider`;
          
        toast({
          title: "Success",
          description: successMessage,
        });
        
        // Refresh the providers list using the hook
        await refreshStatus();
        
        // If this was a new provider, select it
        if (selectedProvider === 'new' && data.id) {
          setSelectedProvider(data.id.toString());
        }
        
        // Notify parent component about the provider update
        if (onProviderUpdate) {
          onProviderUpdate(config.provider);
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save provider settings");
      }
    } catch (error: any) {
      console.error("Error saving provider:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to save provider settings",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>LLM Provider Settings</CardTitle>
        <CardDescription>
          Configure and manage your LLM providers
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div>
              <Label htmlFor="provider-select">Select Provider</Label>
              <Select 
                value={selectedProvider} 
                onValueChange={handleProviderSelect}
                disabled={isSaving}
              >
                <SelectTrigger id="provider-select" className="mt-1">
                  <SelectValue placeholder="Select a provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="new">+ Add New Provider</SelectItem>
                  {allProviders.map((provider) => (
                    provider.id ? (
                      <SelectItem 
                        key={provider.id} 
                        value={provider.id.toString()}
                        className="flex items-center justify-between"
                      >
                        <div className="flex items-center">
                          <span>{provider.name}</span>
                          {provider.is_active && (
                            <Badge variant="outline" className="ml-2">Active</Badge>
                          )}
                        </div>
                      </SelectItem>
                    ) : null
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {selectedProvider && (
              <div className="space-y-4 pt-4 border-t">
                <div>
                  <Label htmlFor="name">Provider Name</Label>
                  <Input
                    id="name"
                    name="name"
                    value={config.name || ""}
                    onChange={handleInputChange}
                    placeholder="e.g., My OpenAI Account"
                    required
                    disabled={isSaving}
                  />
                </div>
                
                {selectedProvider === 'new' && (
                  <div>
                    <Label htmlFor="provider-type">Provider Type</Label>
                    <Select 
                      value={config.provider} 
                      onValueChange={(value: ProviderType) => handleProviderTypeChange(value)}
                      disabled={isSaving}
                    >
                      <SelectTrigger id="provider-type" className="mt-1">
                        <SelectValue placeholder="Select provider type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openai">OpenAI</SelectItem>
                        <SelectItem value="azure">Azure OpenAI</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

              </div>
            )}
          </div>

          {selectedProvider && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="apiKey">
                  {config.provider === "openai" ? "OpenAI" : "Azure"} API Key
                </Label>
                <Input
                  id="apiKey"
                  name="apiKey"
                  type="password"
                  value={config.apiKey || ""}
                  onChange={handleInputChange}
                  placeholder={`Enter your ${config.provider === "openai" ? "OpenAI" : "Azure"} API key`}
                  required
                  disabled={isSaving}
                />
              </div>

              <div>
                <Label htmlFor="model">Model</Label>
                <Input
                  id="model"
                  name="model"
                  value={config.model || ""}
                  onChange={handleInputChange}
                  placeholder="gpt-4"
                  required
                  disabled={isSaving}
                />
              </div>

              {config.provider === "azure" && (
              <>
                <div>
                  <Label htmlFor="endpoint">Endpoint</Label>
                  <Input
                    id="endpoint"
                    name="endpoint"
                    value={config.endpoint || ""}
                    onChange={handleInputChange}
                    placeholder="https://your-resource.openai.azure.com/"
                    required
                    disabled={isSaving}
                  />
                </div>

                <div>
                  <Label htmlFor="deployment">Deployment Name</Label>
                  <Input
                    id="deployment"
                    name="deployment"
                    value={config.deployment || ""}
                    onChange={handleInputChange}
                    placeholder="your-deployment-name"
                    required
                    disabled={isSaving}
                  />
                </div>

                <div>
                  <Label htmlFor="apiVersion">API Version</Label>
                  <Input
                    id="apiVersion"
                    name="apiVersion"
                    value={config.apiVersion || "2023-05-15"}
                    onChange={handleInputChange}
                    placeholder="2023-05-15"
                    required
                    disabled={isSaving}
                  />
                </div>
              </>
              )}
              </div>
            )}

            {selectedProvider && selectedProvider !== 'new' && (
              <div className="space-y-4">
                {/* Connection Status */}
                <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    {(() => {
                      const provider = allProviders.find(p => p.id?.toString() === selectedProvider);
                      const status = provider?.connection_status || 'untested';
                      
                      if (status === 'connected') {
                        return <CheckCircle className="h-4 w-4 text-green-500" />;
                      } else if (status === 'failed') {
                        return <XCircle className="h-4 w-4 text-red-500" />;
                      } else {
                        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
                      }
                    })()}
                    <span className="text-sm font-medium">
                      Connection: {(() => {
                        const provider = allProviders.find(p => p.id?.toString() === selectedProvider);
                        const status = provider?.connection_status || 'untested';
                        return status.charAt(0).toUpperCase() + status.slice(1);
                      })()}
                      {config.isActive && (
                        <Badge variant="default" className="ml-2">Active Provider</Badge>
                      )}
                      {allProviders.find(p => p.id?.toString() === selectedProvider)?.is_from_env && (
                        <Badge variant="secondary" className="ml-2">From Environment</Badge>
                      )}
                    </span>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={async () => {
                      setIsTestingConnection(true);
                      try {
                        const result = await testProviderConnection(parseInt(selectedProvider));
                        toast({
                          title: result.success ? "Connection Successful" : "Connection Failed",
                          description: result.message,
                          variant: result.success ? "default" : "destructive",
                        });
                      } catch (error) {
                        toast({
                          title: "Test Failed",
                          description: "Unable to test connection",
                          variant: "destructive",
                        });
                      } finally {
                        setIsTestingConnection(false);
                      }
                    }}
                    disabled={isTestingConnection || isSaving}
                  >
                    {isTestingConnection ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Testing...
                      </>
                    ) : (
                      "Test Connection"
                    )}
                  </Button>
                </div>

                {/* Activation Controls */}
                {!config.isActive && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-blue-900">Activate this provider</p>
                        <p className="text-xs text-blue-700">Make this the active provider for new conversations</p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          setIsSaving(true);
                          try {
                            const success = await activateProvider(parseInt(selectedProvider));
                            if (success) {
                              toast({
                                title: "Provider Activated",
                                description: `${config.name} is now the active provider`,
                              });
                              // Update local state
                              setConfig(prev => ({ ...prev, isActive: true }));
                            } else {
                              throw new Error('Failed to activate provider');
                            }
                          } catch (error) {
                            toast({
                              title: "Activation Failed",
                              description: "Unable to activate provider",
                              variant: "destructive",
                            });
                          } finally {
                            setIsSaving(false);
                          }
                        }}
                        disabled={isSaving}
                      >
                        Activate
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {selectedProvider && (
            <div className="flex justify-between pt-4 border-t">
              <div>
                {selectedProvider !== 'new' && selectedProvider !== '' && (
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={handleDeleteProvider}
                    disabled={isSaving || config.isActive}
                    className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                  >
                    Delete Provider
                  </Button>
                )}
              </div>
              <div className="space-x-2">
                <Button 
                  type="button" 
                  variant="outline"
                  onClick={() => router.push('/')}
                  disabled={isSaving}
                >
                  Back to Home
                </Button>
                <Button 
                  type="submit" 
                  disabled={isSaving}
                >
                  {isSaving ? "Saving..." : "Save Settings"}
                </Button>
              </div>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
