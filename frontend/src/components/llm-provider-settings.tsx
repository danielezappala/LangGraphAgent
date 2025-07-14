"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";

type ProviderType = "openai" | "azure";

interface ProviderConfig {
  provider: ProviderType;
  apiKey: string;
  model?: string;
  endpoint?: string;
  deployment?: string;
  apiVersion?: string;
}

export function LLMProviderSettings() {
  const [activeProvider, setActiveProvider] = useState<ProviderType>("openai");
  const [isLoading, setIsLoading] = useState(true);
  const [config, setConfig] = useState<ProviderConfig>({
    provider: "openai",
    apiKey: "",
    model: "gpt-4",
    endpoint: "",
    deployment: "",
    apiVersion: "2023-05-15"
  });
  const { toast } = useToast();
  const router = useRouter();

  // Fetch current provider on component mount
  useEffect(() => {
    const fetchCurrentProvider = async () => {
      try {
        const response = await fetch("/api/providers/active");
        if (response.ok) {
          const data = await response.json();
          setConfig(prev => ({
            ...prev,
            provider: data.provider
          }));
        }
      } catch (error) {
        console.error("Error fetching current provider:", error);
      }
    };

    fetchCurrentProvider();
  }, []);

  // Load current provider settings
  useEffect(() => {
    const loadCurrentProvider = async () => {
      try {
        const response = await fetch("/api/providers/active");
        if (response.ok) {
          const data = await response.json();
          setActiveProvider(data.provider);
          setConfig(prev => ({
            ...prev,
            provider: data.provider
          }));
        }
      } catch (error) {
        console.error("Failed to load provider settings:", error);
        toast({
          title: "Error",
          description: "Failed to load provider settings",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadCurrentProvider();
  }, [toast]);

  const handleProviderChange = (provider: ProviderType) => {
    setActiveProvider(provider);
    setConfig(prev => ({
      ...prev,
      provider,
      // Reset fields when switching providers
      endpoint: provider === "azure" ? prev.endpoint : undefined,
      deployment: provider === "azure" ? prev.deployment : undefined,
      apiVersion: provider === "azure" ? prev.apiVersion : "2023-05-15",
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config.apiKey) {
      toast({
        title: "Error",
        description: "API Key is required",
        variant: "destructive",
      });
      return;
    }
    
    setIsLoading(true);

    try {
      const requestBody: RequestBody = {
        provider: config.provider,
        api_key: config.apiKey,
      };

      // Add provider-specific fields
      if (config.provider === 'openai') {
        if (config.model) {
          requestBody.model = config.model;
        }
      } else { // azure
        if (!config.endpoint) {
          throw new Error("Azure endpoint is required");
        }
        requestBody.endpoint = config.endpoint;
        requestBody.deployment = config.deployment || 'gpt-4';
        requestBody.api_version = config.apiVersion || '2023-05-15';
      }

      const response = await fetch("/api/providers/switch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        toast({
          title: "Success",
          description: `Switched to ${config.provider.toUpperCase()} provider`,
        });
        // Redirect to home page after a short delay to show the success message
        setTimeout(() => {
          router.push('/');
        }, 1000);
      } else {
        throw new Error("Failed to update provider");
      }
    } catch (error) {
      console.error("Error updating provider:", error);
      toast({
        title: "Error",
        description: "Failed to update provider settings",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div>Loading provider settings...</div>;
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>LLM Provider Settings</CardTitle>
        <CardDescription>
          Configure your preferred LLM provider and API settings
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex space-x-4 mb-6">
            <Button
              type="button"
              variant={activeProvider === "openai" ? "default" : "outline"}
              onClick={() => handleProviderChange("openai")}
            >
              OpenAI
            </Button>
            <Button
              type="button"
              variant={activeProvider === "azure" ? "default" : "outline"}
              onClick={() => handleProviderChange("azure")}
            >
              Azure OpenAI
            </Button>
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="apiKey">
                {activeProvider === "openai" ? "OpenAI" : "Azure"} API Key
              </Label>
              <Input
                id="apiKey"
                name="apiKey"
                type="password"
                value={config.apiKey}
                onChange={handleInputChange}
                placeholder={`Enter your ${activeProvider === "openai" ? "OpenAI" : "Azure"} API key`}
                required
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
              />
            </div>

            {activeProvider === "azure" && (
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
                  />
                </div>
              </>
            )}
          </div>

          <div className="flex justify-end">
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Saving..." : "Save Settings"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
