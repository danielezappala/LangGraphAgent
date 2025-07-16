"use client";

import { AppSidebar } from '@/components/app-sidebar';
import { ChatInterface } from '@/components/chat-interface';
import { TopNav } from '@/components/top-nav';
import { SidebarProvider, Sidebar, SidebarInset } from '@/components/ui/sidebar';
import { useState, useEffect, Dispatch, SetStateAction } from 'react';
import { useToast } from '@/hooks/use-toast';
import { v4 as uuidv4 } from 'uuid';
import { Message, Conversation } from "@/lib/types";
import { ProviderAlert } from "@/components/provider-alert";
import { ProviderStatusIndicator } from "@/components/provider-status-indicator";

export default function Home() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [threadId, setThreadId] = useState<string>('');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [emptyConversationId, setEmptyConversationId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string>('default_agent'); // Aggiunto stato per l'agente
  const { toast } = useToast();

  const fetchConversations = async () => {
    setIsLoadingConversations(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/history/`);
      if (!response.ok) {
        throw new Error('Failed to fetch conversations');
      }
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error(error);
      toast({ title: 'Error', description: 'Could not load conversations.', variant: 'destructive' });
    } finally {
      setIsLoadingConversations(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [toast]);

  useEffect(() => {
    const loadConversation = async () => {
      if (!selectedConversationId) {
        // Non resettare il threadId qui, viene gestito da handleNewChat
        // Se non c'è una conversazione selezionata, semplicemente non fare nulla.
        return;
      }

      setIsLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/history/${selectedConversationId}`);
        if (!response.ok) {
          throw new Error('Failed to load conversation history.');
        }
        const data = await response.json();
        let rawMessagesSource = [];

        if (data && typeof data.messages === 'object' && data.messages !== null) {
          if (Array.isArray(data.messages)) {
            rawMessagesSource = data.messages;
          } else {
            rawMessagesSource = Object.values(data.messages);
          }
        }
        
        const transformedMsgs = rawMessagesSource
          .filter((msg: any) => msg && msg.content && (typeof msg.content === 'string' ? msg.content.trim() !== '' : true))
          .map((msg: any) => {
            const baseMessage: Message = {
              role: msg.type === 'human' ? 'user' : 'assistant',
              content: msg.type === 'tool' 
                ? (typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content, null, 2))
                : msg.content,
              id: msg.id || uuidv4(), // Use uuidv4 for id generation if not present
              // @ts-ignore 
              original: msg 
            };
            if (msg.type === 'tool') {
              baseMessage.tool = true;
            }
            return baseMessage;
          });

        if (!data?.conversation || transformedMsgs.length === 0) {
          setEmptyConversationId(selectedConversationId);
        } else {
          setEmptyConversationId(null);
        }
        console.log('Set messages in page.tsx (transformed):', transformedMsgs);
        setMessages(transformedMsgs);
        // data.thread_id è più corretto se disponibile, altrimenti selectedConversationId
        setThreadId(data.thread_id || selectedConversationId); 
      } catch (error) {
        console.error(error);
        setMessages([
          { role: 'assistant', content: 'Sorry, I could not load the conversation history.' }
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    loadConversation();
  }, [selectedConversationId]);

    const handleNewChat = () => {
    setSelectedConversationId(null); // Deseleziona la conversazione per rimuovere l'evidenziazione
    setMessages([]); // Pulisci i messaggi visualizzati
    setThreadId(uuidv4()); // Imposta un nuovo ID univoco per la nuova sessione di chat
    setEmptyConversationId(null);
  };

  const handleDeleteConversation = async (thread_id: string) => {
    try {
      console.log('Attempting to delete conversation with ID:', thread_id);
      
      // Make sure we have a valid thread_id
      if (!thread_id || typeof thread_id !== 'string' || thread_id.trim() === '') {
        console.error('Invalid thread_id provided:', thread_id);
        throw new Error('ID conversazione non valido: ' + thread_id);
      }

      // Log the current conversations for debugging
      console.log('Current conversations before deletion:', conversations);
      
      // Check if the conversation exists in the current list
      const conversationExists = conversations.some(conv => conv.thread_id === thread_id);
      if (!conversationExists) {
        console.error('Conversation not found in current list:', thread_id);
        throw new Error('Conversazione non trovata nella lista corrente');
      }

      // Use the full URL to the backend
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const backendUrl = `${baseUrl}/api/history/${encodeURIComponent(thread_id)}`;
      
      // Log the URL for debugging
      console.log('Deleting conversation with URL:', backendUrl.toString());
      
      const response = await fetch(backendUrl.toString(), {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Delete error response:', response.status, errorText);
        let errorMessage = 'Impossibile eliminare la conversazione';
        
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If we can't parse the error as JSON, use the raw text
          errorMessage = errorText || errorMessage;
        }
        
        throw new Error(errorMessage);
      }

      // Update the conversations list by filtering out the deleted one
      const updatedConversations = conversations.filter((c: Conversation) => c.thread_id !== thread_id);
      setConversations(updatedConversations);

      // If the deleted conversation was the selected one, clear the chat
      if (selectedConversationId === thread_id) {
        setSelectedConversationId(null);
        setMessages([]);
        setThreadId(uuidv4());
      }

      toast({
        title: 'Successo',
        description: 'Conversazione eliminata con successo.',
      });
    } catch (error) {
      console.error(error);
      toast({
        title: 'Errore',
        description: 'Impossibile eliminare la conversazione.',
        variant: 'destructive',
      });
    }
  };

  return (
    <SidebarProvider>
      <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
        <Sidebar>
          <AppSidebar
            conversations={conversations}
            isLoading={isLoadingConversations}
            onSelectConversation={setSelectedConversationId}
            onDeleteConversation={handleDeleteConversation}
            onNewChat={handleNewChat}
          />
        </Sidebar>
        <SidebarInset>
          <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6 h-screen">
            <TopNav />
            {/* Provider Status Indicator */}
            <ProviderStatusIndicator />
            
            {/* Provider Alert (only shows if there are issues) */}
            <ProviderAlert />
            <ChatInterface 
              messages={messages}
              setMessages={setMessages}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              selectedConversationId={selectedConversationId}
              threadId={threadId}
              setThreadId={setThreadId}
              selectedAgent={selectedAgent}
              onAgentChange={setSelectedAgent}
              onConversationUpdate={fetchConversations}
            />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
