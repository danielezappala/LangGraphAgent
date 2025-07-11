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
                <Button
                  key={conv.thread_id}
                  variant="ghost"
                  className="w-full justify-start text-left h-auto py-2"
                  onClick={() => onSelectConversation(conv.thread_id)}
                  title={conv.preview}
                >
                  <div className="truncate">
                    <div className="font-medium text-sm whitespace-normal">
                      {conv.preview || "Nessuna anteprima"}
                    </div>
                    <div className="flex justify-between items-center w-full">
                      <span className="text-xs text-muted-foreground pt-1">
                        {new Date(conv.last_message_ts).toLocaleString('it-IT', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 shrink-0"
                        onClick={(e) => { 
                          e.stopPropagation(); 
                          onDeleteConversation(conv.thread_id); 
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-red-500" />
                      </Button>
                    </div>
                  </div>
                </Button>
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
