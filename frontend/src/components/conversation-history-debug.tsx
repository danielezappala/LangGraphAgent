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
    console.log('Raw timestamp:', timestamp, 'Type:', typeof timestamp);
    
    if (!timestamp) {
      console.log('No timestamp provided');
      return 'No date';
    }
    
    try {
      let date: Date;
      
      // Handle ISO 8601 string format (e.g., '2023-07-14T12:34:56.789Z')
      if (typeof timestamp === 'string' && timestamp.includes('T')) {
        console.log('Parsing as ISO 8601 string');
        date = new Date(timestamp);
      } 
      // Handle numeric string or number (legacy support)
      else {
        console.log('Parsing as numeric timestamp');
        const ts = typeof timestamp === 'string' ? parseInt(timestamp, 10) : timestamp;
        console.log('Parsed timestamp:', ts, 'Type:', typeof ts);
        
        if (isNaN(ts)) {
          console.error('Invalid timestamp (not a number):', timestamp);
          return 'Invalid date';
        }
        
        // If the timestamp is in nanoseconds (from the backend), convert to milliseconds
        const isNanoseconds = ts > 1e16; // If timestamp is greater than 10^16, it's likely in nanoseconds
        const msTimestamp = isNanoseconds ? Math.floor(ts / 1000000) : ts;
        console.log('Converted to ms:', msTimestamp, 'isNanoseconds:', isNanoseconds);
        
        date = new Date(msTimestamp);
      }
      
      console.log('Date object:', date);
      
      // Check if the date is valid
      if (isNaN(date.getTime())) {
        console.error('Invalid date from timestamp:', timestamp);
        return 'Invalid date';
      }
      
      // Format the date in a user-friendly way
      const formattedDate = date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
      
      console.log('Formatted date:', formattedDate);
      return formattedDate;
    } catch (e) {
      console.error('Error formatting date:', e, 'Timestamp was:', timestamp);
      return 'Error';
    }
  };

  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="item-1" className="border-0">
        <AccordionTrigger className="py-2 px-4 hover:no-underline [&>svg]:h-4 [&>svg]:w-4">
          <div className="flex items-center justify-start w-full gap-2">
            <History className="h-4 w-4 flex-shrink-0" />
            <span className="text-left">Chat History</span>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          {isLoading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          ) : !isLoading && conversations.length > 0 ? (
            <div className="space-y-1">
              {conversations.map((conv) => {
                console.log('Conversation:', {
                  thread_id: conv.thread_id,
                  last_message_ts: conv.last_message_ts,
                  preview: conv.preview
                });
                
                return (
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
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground p-2">No previous conversations</p>
          )}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
