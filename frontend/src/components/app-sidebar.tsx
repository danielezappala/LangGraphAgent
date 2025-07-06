"use client";

import { Sidebar, SidebarHeader, SidebarContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton } from "@/components/ui/sidebar";
import { AgentsMenu } from "@/components/agents-menu";
import { MessageSquare, History } from "lucide-react";
import { RediLogo } from "@/components/icons";
import { cn } from "@/lib/utils";

interface AppSidebarProps {
  selectedAgent?: string;
  onAgentChange?: (agent: string) => void;
}

export function AppSidebar({ selectedAgent, onAgentChange }: AppSidebarProps) {
  return (
    <Sidebar side="left" collapsible="icon" className="hidden border-r bg-card md:flex md:flex-col">
      <SidebarHeader>
        <div className="flex items-center gap-2 group-data-[collapsible=icon]:justify-center">
          {/* Redi SVG Icon */}
          <span className={cn("text-lg font-semibold group-data-[collapsible=icon]:hidden flex items-center")}>{/* eslint-disable-next-line @next/next/no-img-element */}
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 64 64" className="mr-2"><rect width="64" height="64" rx="12" fill="#2563eb"/><text x="50%" y="56%" textAnchor="middle" fill="white" fontFamily="Arial, Helvetica, sans-serif" fontSize="38" fontWeight="bold" dy=".1em">R</text></svg>
            Redi
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton tooltip="New Chat" isActive>
              <MessageSquare />
              <span>New Chat</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <AgentsMenu onAgentChange={onAgentChange} selectedAgent={selectedAgent} />
        </SidebarMenu>
      </SidebarContent>
    </Sidebar>
  );
}
