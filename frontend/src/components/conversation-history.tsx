"use client";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Loader2, Trash2, History } from "lucide-react";
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

  const formatDate = (timestamp: string | number | null | undefined) => {
    if (!timestamp) return 'No date';
    
    try {
      // Convert the timestamp to a number if it's a string
      const ts = typeof timestamp === 'string' ? parseInt(timestamp, 10) : timestamp;
      
      // If the timestamp is in nanoseconds (from the backend), convert to milliseconds
      const isNanoseconds = ts > 1e16; // If timestamp is greater than 10^16, it's likely in nanoseconds
      const date = isNanoseconds 
        ? new Date(ts / 1000000) // Convert nanoseconds to milliseconds
        : new Date(ts);
      
      // Check if the date is valid
      if (isNaN(date.getTime())) {
        console.error('Invalid date:', timestamp);
        return 'Invalid date';
      }
      
      // Format the date in a user-friendly way
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    } catch (e) {
      console.error('Error formatting date:', e);
      return 'Invalid date';
    }
  };

  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="item-1">
        <AccordionTrigger className="[&>svg]:h-4 [&>svg]:w-4">
          <History className="mr-2" />
          <span>Chat History</span>
        </AccordionTrigger>
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
                      {conv.preview || "No preview"}
                    </div>
                    <div className="text-xs text-muted-foreground pt-1">
                      {formatDate(conv.last_message_ts)}
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
            <p className="text-sm text-muted-foreground p-2">No previous conversations</p>
          )}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
