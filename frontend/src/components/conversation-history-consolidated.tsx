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
  debugMode?: boolean;
}

export function ConversationHistory({ 
  conversations, 
  isLoading, 
  onSelectConversation, 
  onDeleteConversation,
  debugMode = false
}: ConversationHistoryProps) {

  const formatDate = (timestamp: string | number | null | undefined) => {
    if (debugMode) {
      console.log('Raw timestamp:', timestamp, 'Type:', typeof timestamp);
    }
    
    if (!timestamp) {
      if (debugMode) {
        console.log('No timestamp provided');
      }
      return 'No date';
    }
    
    try {
      let date: Date;
      
      // Handle ISO 8601 string format (e.g., '2025-07-14T21:31:39.445833+00:00')
      if (typeof timestamp === 'string' && timestamp.includes('T')) {
        if (debugMode) {
          console.log('Parsing as ISO 8601 string');
        }
        date = new Date(timestamp);
      } 
      // Handle numeric string or number (legacy support)
      else {
        if (debugMode) {
          console.log('Parsing as numeric timestamp');
        }
        const ts = typeof timestamp === 'string' ? parseInt(timestamp, 10) : timestamp;
        
        if (debugMode) {
          console.log('Parsed timestamp:', ts, 'Type:', typeof ts);
        }
        
        if (isNaN(ts)) {
          console.error('Invalid timestamp (not a number):', timestamp);
          return 'Invalid date';
        }
        
        // If the timestamp is in nanoseconds, convert to milliseconds
        const isNanoseconds = ts > 1e16; // If timestamp is greater than 10^16, it's likely in nanoseconds
        const msTimestamp = isNanoseconds ? Math.floor(ts / 1000000) : ts;
        
        if (debugMode) {
          console.log('Converted to ms:', msTimestamp, 'isNanoseconds:', isNanoseconds);
        }
        
        date = new Date(msTimestamp);
      }
      
      if (debugMode) {
        console.log('Date object:', date);
      }
      
      // Check if the date is valid
      if (isNaN(date.getTime())) {
        console.error('Invalid date:', timestamp);
        return 'Invalid date';
      }
      
      // Use sophisticated relative time formatting unless in debug mode
      if (!debugMode) {
        const now = new Date();
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
        
        // Format as relative time if less than 24 hours ago
        if (diffInSeconds < 60) {
          return 'Just now';
        } else if (diffInSeconds < 3600) {
          const minutes = Math.floor(diffInSeconds / 60);
          return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
        } else if (diffInSeconds < 86400) { // Less than 24 hours
          const hours = Math.floor(diffInSeconds / 3600);
          return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
        } 
        // For older dates, show the date and time
        const isThisYear = date.getFullYear() === now.getFullYear();
        
        if (isThisYear) {
          // For dates in the current year, show month, day, and time
          return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          });
        } else {
          // For older dates, include the year
          return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
          });
        }
      } else {
        // Debug mode: simple format
        const formattedDate = date.toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });
        
        if (debugMode) {
          console.log('Formatted date:', formattedDate);
        }
        return formattedDate;
      }
    } catch (e) {
      console.error('Error formatting date:', e, 'Timestamp was:', timestamp);
      return debugMode ? 'Error' : 'Invalid date';
    }
  };

  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="item-1" className={debugMode ? "border-0" : ""}>
        <AccordionTrigger className={`${debugMode ? "py-2 px-4 hover:no-underline" : ""} [&>svg]:h-4 [&>svg]:w-4`}>
          {debugMode ? (
            <div className="flex items-center justify-start w-full gap-2">
              <History className="h-4 w-4 flex-shrink-0" />
              <span className="text-left">Chat History</span>
            </div>
          ) : (
            <>
              <History className="mr-2" />
              <span>Chat History</span>
            </>
          )}
        </AccordionTrigger>
        <AccordionContent>
          {isLoading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          ) : !isLoading && conversations.length > 0 ? (
            <div className="space-y-1">
              {conversations.map((conv) => {
                if (debugMode) {
                  console.log('Conversation:', {
                    thread_id: conv.thread_id,
                    last_message_ts: conv.last_message_ts,
                    preview: conv.preview
                  });
                }
                
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