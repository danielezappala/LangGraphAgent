"use client";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Loader2, Trash2 } from "lucide-react";
import { Conversation, Message } from "@/lib/types";

interface ConversationHistoryProps {
  conversations: Conversation[];
  isLoading: boolean;
  onSelectConversation: (conversationId: string) => void;
  onDeleteConversation: (id: string) => void;
}

export function ConversationHistory({ 
  conversations, 
  isLoading, 
  onSelectConversation, 
  onDeleteConversation 
}: ConversationHistoryProps) {

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
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="item-1">
        <AccordionTrigger>Conversazioni Passate</AccordionTrigger>
        <AccordionContent>
          {isLoading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          ) : !isLoading && conversations.length > 0 ? (
            <div className="space-y-1">
              {conversations.map((conv) => (
                <div 
                  key={conv.thread_id}
                  className="relative group w-full text-left py-2 px-4 rounded-md hover:bg-accent hover:text-accent-foreground cursor-pointer"
                  onClick={() => onSelectConversation(conv.thread_id)}
                  title={conv.preview}
                >
                  <div className="pr-8">
                    <div className="font-medium text-sm whitespace-normal">
                      {conv.preview || "Nessuna anteprima"}
                    </div>
                    <div className="text-xs text-muted-foreground pt-1">
                      {new Date(conv.last_message_ts).toLocaleString('it-IT', { 
                        day: '2-digit', 
                        month: 'short', 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </div>
                  </div>
                  <button
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 p-0 m-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-full hover:bg-accent/50"
                    onClick={(e) => { 
                      e.stopPropagation(); 
                      onDeleteConversation(conv.thread_id); 
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground hover:text-red-500" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground p-2">Nessuna conversazione passata.</p>
          )}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
