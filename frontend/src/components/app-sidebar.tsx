"use client";

import { Sidebar, SidebarHeader, SidebarContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton } from "@/components/ui/sidebar";
import { AgentsMenu } from "@/components/agents-menu";
import type { Message } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ConversationHistory } from "./conversation-history-consolidated";
import { MessageSquare } from "lucide-react";
import Link from "next/link";

// Definizione del tipo Conversation, allineato con page.tsx e il backend
interface Conversation {
  thread_id: string;
  last_message_ts: string;
  preview: string;
}

interface AppSidebarProps {
  conversations: Conversation[];
  isLoading: boolean;
  onSelectConversation: (conversationId: string | null) => void;
  onDeleteConversation: (id: string) => void;
  onNewChat: () => void;
}

export function AppSidebar({ 
  conversations,
  isLoading,
  onSelectConversation,
  onDeleteConversation,
  onNewChat
}: AppSidebarProps) {
  return (
    <Sidebar side="left" collapsible="icon" className="hidden border-r bg-card md:flex md:flex-col">
      <SidebarHeader>
        <div className="flex items-center gap-2 group-data-[collapsible=icon]:justify-center">
          <span className={cn("text-lg font-semibold group-data-[collapsible=icon]:hidden flex items-center")}>
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 64 64" className="mr-2"><rect width="64" height="64" rx="12" fill="#2563eb"/><text x="50%" y="56%" textAnchor="middle" fill="white" fontFamily="Arial, Helvetica, sans-serif" fontSize="38" fontWeight="bold" dy=".1em">R</text></svg>
            Redi
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent className="flex flex-col">
        <div className="p-2">
          <button
            onClick={onNewChat}
            className="w-full text-left py-2 px-4 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors flex items-center justify-start gap-2"
          >
            <MessageSquare className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">New Chat</span>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          <ConversationHistory 
            conversations={conversations}
            isLoading={isLoading}
            onSelectConversation={onSelectConversation} 
            onDeleteConversation={onDeleteConversation}
          />
        </div>
      </SidebarContent>

    </Sidebar>
  );
}
