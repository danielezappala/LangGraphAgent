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

type ProviderType = "openai" | "azure";

interface ProviderConfig {
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
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [config, setConfig] = useState<ProviderConfig>({
    name: "",
    provider: "openai",
    apiKey: "",
    model: "gpt-4",
    endpoint: "",
    deployment: "",
    apiVersion: "2023-05-15",
    isActive: false
  });
  const { toast } = useToast();
  const router = useRouter();

  // Fetch all providers and set the active one
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        setIsLoading(true);
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:30010';
        const [providersRes, activeRes] = await Promise.all([
          fetch(`${baseUrl}/api/providers/list`),
          fetch(`${baseUrl}/api/providers/active`)
        ]);

        if (providersRes.ok && activeRes.ok) {
          const providersData = await providersRes.json();
          const activeData = await activeRes.json();
          
          setProviders(providersData);
          
          if (activeData) {
            setConfig(activeData);
            setSelectedProvider(activeData.id ? activeData.id.toString() : "new");
          }
        }
      } catch (error) {
        console.error("Failed to load providers:", error);
        toast({
          title: "Error",
          description: "Failed to load provider settings",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchProviders();
  }, [toast]);

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
      const provider = providers.find(p => p.id?.toString() === id);
      if (provider) {
        setConfig({
          ...provider,
          isActive: provider.isActive || false
        });
      }
    }
  };
  
  const handleProviderTypeChange = (providerType: ProviderType) => {
    setConfig(prev => ({
      ...prev,
      provider: providerType,
      // Reset fields when switching provider types
      endpoint: providerType === "azure" ? prev.endpoint : undefined,
      deployment: providerType === "azure" ? prev.deployment : undefined,
      apiVersion: providerType === "azure" ? (prev.apiVersion || "2023-05-15") : undefined,
    }));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: value,
    }));
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

    try {
      setIsSaving(true);
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:30010';
      const response = await fetch(`${baseUrl}/api/providers/${selectedProvider}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete provider');
      }

      // Refresh the providers list
      await fetchProviders();
      
      // Reset the form
      setSelectedProvider('new');
      setConfig({
        name: '',
        provider: 'openai',
        apiKey: '',
        model: 'gpt-4',
        isActive: false
      });

      toast({
        title: 'Success',
        description: 'Provider deleted successfully',
      });
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
        model: config.model || 'gpt-4',
        is_active: true,
        // Campi specifici per Azure
        ...(config.provider === 'azure' && {
          endpoint: config.endpoint,
          deployment: config.deployment || 'gpt-4',
          api_version: config.apiVersion || '2023-05-15'
        })
      };

      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:30010';
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
        
        // Refresh the providers list
        const providersRes = await fetch("/api/providers/list");
        if (providersRes.ok) {
          const providersData = await providersRes.json();
          setProviders(providersData);
          
          // If this was a new provider, select it
          if (selectedProvider === 'new' && data.id) {
            setSelectedProvider(data.id.toString());
          }
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
                  {providers.map((provider) => (
                    <SelectItem 
                      key={provider.id} 
                      value={provider.id?.toString() || ''}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center">
                        <span>{provider.name}</span>
                        {provider.isActive && (
                          <Badge variant="outline" className="ml-2">Active</Badge>
                        )}
                      </div>
                    </SelectItem>
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
                
                <div className="flex space-x-4 pt-2">
                  <Button
                    type="button"
                    variant={config.provider === "openai" ? "default" : "outline"}
                    onClick={() => handleProviderTypeChange("openai")}
                    disabled={isSaving}
                    className="flex-1"
                  >
                    OpenAI
                  </Button>
                  <Button
                    type="button"
                    variant={config.provider === "azure" ? "default" : "outline"}
                    onClick={() => handleProviderTypeChange("azure")}
                    disabled={isSaving}
                    className="flex-1"
                  >
                    Azure OpenAI
                  </Button>
                </div>
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
                  onClick={() => router.back()}
                  disabled={isSaving}
                >
                  Cancel
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
