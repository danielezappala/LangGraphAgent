"use client";
import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Loader2, X } from "lucide-react";

interface HistoryModalProps {
  agentId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectMessage?: (message: string) => void;
}

// Interfaccia per i messaggi nella cronologia
export interface HistoryMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

// Interfaccia per le conversazioni nella lista
export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  preview?: string;
}

export function HistoryModal({ 
  agentId, 
  open, 
  onOpenChange,
  onSelectMessage 
}: HistoryModalProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<HistoryMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);

  // Carica l'elenco delle conversazioni
  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/history')
      .then(async (res) => {
        if (!res.ok) throw new Error("Errore nel caricamento della cronologia");
        return res.json();
      })
      .then((data) => {
        setError(null);
        setConversations(data.conversations || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    } catch (err) {
      console.error('Errore nel caricamento delle conversazioni:', err);
      setError('Errore nel caricamento della cronologia');
      return [];
    } finally {
      setLoading(false);
    }
  };

  // Carica i messaggi di una conversazione specifica
  const loadConversation = async (conversationId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/history/${conversationId}`);
      
      if (!response.ok) {
        throw new Error('Impossibile caricare la conversazione');
      }
      
      const data = await response.json();
      setMessages(data.messages || []);
      setSelectedConversation(conversationId);
    } catch (err) {
      console.error('Errore nel caricamento della conversazione:', err);
      setError('Errore nel caricamento della conversazione');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      loadConversations();
    } else {
      // Reset degli stati quando il modal viene chiuso
      setMessages([]);
      setConversations([]);
      setSelectedConversation(null);
      setError(null);
    }
  }, [open]);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl w-[90%] max-h-[90vh] flex flex-col">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle>
            {selectedConversation ? 'Dettagli conversazione' : 'Cronologia conversazioni'}
          </DialogTitle>
          {/* Solo un pulsante custom per la chiusura */}
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onOpenChange(false)}>
            <X className="h-4 w-4" />
          </Button>
        </DialogHeader>
        
        <div className="flex-1 overflow-hidden flex">
          {/* Sidebar con elenco conversazioni */}
          <div className="w-64 border-r pr-4 overflow-y-auto">
            <h3 className="font-medium mb-2">Conversazioni recenti</h3>
            {loading && !selectedConversation ? (
              <div className="flex justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
              </div>
            ) : error && conversations.length === 0 ? (
              <div className="text-red-500 text-sm p-2 bg-red-50 rounded">
                {error}
              </div>
            ) : (
              <div className="space-y-1">
                {!selectedConversation && conversations.length === 0 && !error && (
                  <p className="text-sm text-muted-foreground">Al momento non ci sono conversazioni</p>
                )}
                
                {!selectedConversation && conversations.length > 0 && (
                  <div className="space-y-1">
                    {conversations.map((conv) => (
                      <Button
                        key={conv.id}
                        variant="ghost"
                        className={`w-full justify-start text-left h-auto py-2 ${selectedConversation === conv.id ? 'bg-accent' : ''}`}
                        onClick={() => loadConversation(conv.id)}
                      >
                        <div className="truncate">
                          <div className="font-medium">
                            {conv.title || `Conversazione del ${new Date(conv.created_at).toLocaleDateString('it-IT')}`}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatDate(conv.created_at)}
                          </div>
                        </div>
                      </Button>
                    ))}
                  </div>
                )}
                
                {selectedConversation && (
                  <Button 
                    variant="ghost" 
                    className="w-full justify-start text-sm"
                    onClick={() => setSelectedConversation(null)}
                  >
                    ← Torna all'elenco
                  </Button>
                )}
              </div>
            )}
          </div>
          
          {/* Area di visualizzazione messaggi */}
          <div className="flex-1 overflow-hidden flex flex-col pl-4">
            {selectedConversation ? (
              <>
                <ScrollArea className="flex-1 pr-2">
                  <div className="space-y-4">
                    {loading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      </div>
                    ) : error ? (
                      <div className="text-red-500 p-4 bg-red-50 rounded">
                        {error}
                      </div>
                    ) : messages.length === 0 ? (
                      <div className="text-center text-muted-foreground py-8">
                        Nessun messaggio in questa conversazione
                      </div>
                    ) : (
                      messages.map((message) => (
                        <div
                          key={message.id}
                          className={`p-4 rounded-lg ${
                            message.role === 'user'
                              ? 'bg-blue-50 text-blue-900 ml-8'
                              : 'bg-gray-50 text-gray-900 mr-8'
                          }`}
                          onClick={() => onSelectMessage?.(message.content)}
                        >
                          <div className="flex justify-between items-start mb-1">
                            <span className="font-medium">
                              {message.role === 'user' ? 'Tu' : 'Assistente'}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {formatDate(message.timestamp)}
                            </span>
                          </div>
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
                
                {onSelectMessage && messages.length > 0 && (
                  <div className="pt-4 border-t mt-4">
                    <Button 
                      variant="outline" 
                      className="w-full"
                      onClick={() => {
                        const lastUserMessage = [...messages]
                          .reverse()
                          .find(m => m.role === 'user');
                        if (lastUserMessage) {
                          onSelectMessage(lastUserMessage.content);
                        }
                        onOpenChange(false);
                      }}
                    >
                      Riprendi questa conversazione
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Seleziona una conversazione per visualizzare i dettagli
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
