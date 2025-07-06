"use client";

import { useState, useEffect } from "react";
import { fetchAgents, fetchAgentDetails, AgentSummary, AgentDetails } from "@/app/api/agents";
import { AgentSettings } from "@/components/agent-settings";
import { SidebarMenuItem, SidebarMenuButton } from "@/components/ui/sidebar";
import { Bot } from "lucide-react";
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select";

// Gli agenti ora sono caricati dinamicamente dal backend

interface AgentsMenuProps {
  selectedAgent?: string;
  onAgentChange?: (agent: string) => void;
}

export function AgentsMenu({ selectedAgent, onAgentChange }: AgentsMenuProps) {
  const [agents, setAgents] = useState<AgentSummary[]>([]);

  const [details, setDetails] = useState<AgentDetails | null>(null);

  useEffect(() => {
    fetchAgents().then(setAgents);
  }, []);

  useEffect(() => {
    if (selectedAgent) fetchAgentDetails(selectedAgent).then(setDetails);
  }, [selectedAgent]);

  function handleChange(agentId: string) {
    onAgentChange?.(agentId);
  }

  const [showSettings, setShowSettings] = useState(false);

  return (
    <SidebarMenuItem>
      <SidebarMenuButton tooltip="Agents">
        <Bot />
        <span>Agents</span>
      </SidebarMenuButton>
      <div className="pl-8 pr-2 pt-2">
        <Select value={selectedAgent} onValueChange={handleChange}>
          <SelectTrigger>
            <SelectValue placeholder="Select agent" />
          </SelectTrigger>
          <SelectContent>
            {agents.map((agent) => (
              <SelectItem key={agent.id} value={agent.id}>{agent.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {selectedAgent && (
          <button
            className="mt-2 px-3 py-1 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/80 transition"
            onClick={() => setShowSettings(true)}
          >
            Settings
          </button>
        )}
        {showSettings && selectedAgent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="bg-card rounded-lg shadow-lg max-w-lg w-full relative">
              <button className="absolute top-2 right-2 text-xl" onClick={() => setShowSettings(false)}>&times;</button>
              <AgentSettings agentId={selectedAgent} />
            </div>
          </div>
        )}
        {details && (
          <div className="mt-4 text-xs bg-muted rounded p-2">
            <div><b>LLM:</b> {details.llm}</div>
            <div><b>Prompt:</b> <pre className="whitespace-pre-wrap break-words max-h-32 overflow-auto">{JSON.stringify(details.prompt, null, 2)}</pre></div>
            <div><b>Grafo:</b> {details.grafo}</div>
          </div>
        )}
      </div>
    </SidebarMenuItem>
  );
}
