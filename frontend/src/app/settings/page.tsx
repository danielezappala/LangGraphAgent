"use client";

import { useState, useEffect } from "react";
import { LLMProviderSettings } from "@/components/llm-provider-settings";
import { Badge } from "@/components/ui/badge";

export default function SettingsPage() {
  const [activeProvider, setActiveProvider] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchActiveProvider = async () => {
      try {
        const response = await fetch("/api/providers/active");
        if (response.ok) {
          const data = await response.json();
          setActiveProvider(data.provider || "Not set");
        }
      } catch (error) {
        console.error("Error fetching active provider:", error);
        setActiveProvider("Error loading provider");
      } finally {
        setIsLoading(false);
      }
    };

    fetchActiveProvider();
  }, []);

  const handleProviderUpdated = (provider: string) => {
    setActiveProvider(provider);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Settings</h1>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-muted-foreground">Current Provider:</span>
          {isLoading ? (
            <div className="h-4 w-20 bg-muted animate-pulse rounded" />
          ) : (
            <Badge variant="outline" className="font-mono text-sm">
              {activeProvider.toUpperCase()}
            </Badge>
          )}
        </div>
      </div>
      <div className="space-y-8">
        <LLMProviderSettings onProviderUpdate={handleProviderUpdated} />
      </div>
    </div>
  );
}
