"use client";

import { AppSidebar } from '@/components/app-sidebar';
import { ChatInterface } from '@/components/chat-interface';
import { TopNav } from '@/components/top-nav';
import { SidebarProvider, Sidebar, SidebarInset } from '@/components/ui/sidebar';
import { useState, useEffect, Dispatch, SetStateAction } from 'react';
import { useToast } from '@/hooks/use-toast';
import { v4 as uuidv4 } from 'uuid';

// Definizione dei tipi
interface Message {
  role: 'user' | 'assistant';
  content: string;
  id?: string;
}

interface Conversation {
  thread_id: string;
  last_message_ts: string;
  preview: string;
}

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

  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoadingConversations(true);
      try {
        const response = await fetch('/api/history/');
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
        const response = await fetch(`/api/history/${selectedConversationId}`);
        if (!response.ok) {
          throw new Error('Failed to load conversation history.');
        }
        const data = await response.json();
        // Gestione sicura di data.conversation e data.conversation.messages
        const msgs = data?.conversation?.messages || [];
        if (!data?.conversation || msgs.length === 0) {

          setEmptyConversationId(selectedConversationId);
        } else {
          setEmptyConversationId(null);
        }
        setMessages(msgs);
        setThreadId(selectedConversationId);
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

  const handleDeleteConversation = async (id: string) => {
    try {
      const response = await fetch(`/api/history/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete conversation.');
      }
      toast({
        title: 'Successo',
        description: 'Conversazione eliminata con successo.',
      });
      // Aggiorna la lista delle conversazioni
      const updatedConversations = conversations.filter((c: Conversation) => c.thread_id !== id);
      setConversations(updatedConversations);
      // Se la conversazione eliminata era quella selezionata, pulisci la chat
      if (selectedConversationId === id) {
        setSelectedConversationId(null);
        setMessages([]);
        setThreadId(uuidv4()); // Preparati per una nuova chat
      }
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
            />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
