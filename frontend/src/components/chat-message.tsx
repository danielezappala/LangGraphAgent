"use client";

import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { RediLogo } from "@/components/icons";
import { Message } from "@/lib/types";
import { Wrench } from "lucide-react";

export const ChatMessage = ({ message }: { message: Message }) => {
    console.log('Rendering single message:', message);

    if (message.tool && typeof message.content === 'string') {
        let toolTitle = "Tool Invoked";
        let isJsonContent = false;
        
        if (message.tool_name) {
            toolTitle = `Tool: ${message.tool_name}`;
        }

        try {
            JSON.parse(message.content);
            isJsonContent = true; 
            
            if (!message.tool_name) {
                const parsedForTitle = JSON.parse(message.content);
                if (parsedForTitle && typeof parsedForTitle.query === 'string') {
                    toolTitle = `Tool: ${parsedForTitle.query}`;
                } else if (parsedForTitle && typeof parsedForTitle.expression === 'string') {
                    toolTitle = `Tool: ${parsedForTitle.expression}`;
                } else {
                    toolTitle = "Tool Output (JSON)";
                }
            }
        } catch (e) {
            isJsonContent = false;
            if (!message.tool_name) {
                toolTitle = "Tool Output"; 
            }
        }

        return (
            <div className="flex items-start gap-4 animate-in fade-in">
                <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                        <Wrench className="h-5 w-5" />
                    </AvatarFallback>
                </Avatar>
                <div className={cn(
                    "flex max-w-[80%] flex-col gap-1 rounded-lg p-3 text-sm shadow-sm",
                    "bg-card border"
                )}>
                    <p className="font-semibold text-foreground">{toolTitle}</p>
                    {isJsonContent ? (
                        <details className="mt-1">
                            <summary className="text-xs text-muted-foreground cursor-pointer">View JSON Details</summary>
                            <p className="whitespace-pre-wrap font-mono text-xs text-muted-foreground mt-1">
                                {message.content} 
                            </p>
                        </details>
                    ) : (
                        <p className="whitespace-pre-wrap text-xs text-muted-foreground mt-1">
                            {message.content}
                        </p>
                    )}
                </div>
            </div>
        );
    }
    
    const isAssistant = message.role === 'assistant';

    return (
        <div className={cn("flex items-start gap-4 animate-in fade-in", isAssistant ? "" : "flex-row-reverse")}>
            <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className={cn(isAssistant ? "bg-transparent" : "bg-primary text-primary-foreground")}>
                    {isAssistant ? <RediLogo className="h-6 w-6 text-primary"/> : 'U'}
                </AvatarFallback>
            </Avatar>
            <div className={cn(
                "flex max-w-[80%] flex-col gap-2 rounded-lg p-3 text-sm shadow-sm",
                isAssistant ? "bg-card border" : "bg-primary text-primary-foreground"
            )}>
                <p className={cn("whitespace-pre-wrap", isAssistant ? "text-muted-foreground" : "text-primary-foreground")}>
                    {message.content}
                </p>
            </div>
        </div>
    );
}
