"use client";

import { AppSidebar } from '@/components/app-sidebar';
import { ChatInterface } from '@/components/chat-interface';
import { TopNav } from '@/components/top-nav';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';

import { useState } from 'react';

export default function Home() {
  const [selectedAgent, setSelectedAgent] = useState<string | undefined>(undefined);
  return (
    <SidebarProvider>
      <div className="relative flex min-h-screen w-full bg-muted/40">
        <AppSidebar selectedAgent={selectedAgent} onAgentChange={setSelectedAgent} />
        <SidebarInset className="flex flex-col">
          <TopNav />
          <main className="flex-1 flex flex-col gap-4 p-4 lg:gap-6 lg:p-6 overflow-hidden">
            <ChatInterface selectedAgent={selectedAgent} onAgentChange={setSelectedAgent} />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
