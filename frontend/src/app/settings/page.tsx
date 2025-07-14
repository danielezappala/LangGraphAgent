"use client";

import { LLMProviderSettings } from "@/components/llm-provider-settings";

export default function SettingsPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>
      <div className="space-y-8">
        <LLMProviderSettings />
      </div>
    </div>
  );
}
