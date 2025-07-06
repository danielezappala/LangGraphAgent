"use client";

import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { RediLogo } from "@/components/icons";

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const ChatMessage = ({ message }: { message: Message }) => {
    const isAssistant = message.role === 'assistant';

    return (
        <div className={cn("flex items-start gap-4 animate-in fade-in", isAssistant ? "" : "flex-row-reverse")}>
            <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className={cn(isAssistant ? "bg-transparent" : "bg-accent text-accent-foreground")}>
                    {isAssistant ? <RediLogo className="h-6 w-6 text-primary"/> : 'U'}
                </AvatarFallback>
            </Avatar>
            <div className={cn(
                "flex max-w-[80%] flex-col gap-2 rounded-lg p-3 text-sm shadow-sm",
                isAssistant ? "bg-card border" : "bg-primary text-primary-foreground"
            )}>
                <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
        </div>
    );
}
