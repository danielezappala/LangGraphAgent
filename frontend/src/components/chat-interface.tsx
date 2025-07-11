"use client";

import { useState, useRef, useEffect, FormEvent } from 'react';
import { AgentsMenu } from '@/components/agents-menu';
import { chatWithAgent } from '@/app/api/agents';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, LoaderCircle } from "lucide-react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { RediLogo } from '@/components/icons';
import { getAiResponse } from '@/app/actions';
import { ChatMessage } from '@/components/chat-message';
import { Message } from "@/lib/types"; 
import { generatePromptStarter } from '@/ai/flows/generate-prompt-starter';

const PromptSuggestion = ({ prompt, onSelect }: { prompt: string, onSelect: (prompt: string) => void }) => {
    return (
        <Button variant="outline" className="text-left h-auto p-4 leading-normal w-full break-words whitespace-normal min-h-[56px] mb-2" onClick={() => onSelect(prompt)}>
            {prompt}
        </Button>
    )
}

interface ChatInterfaceProps {
  selectedAgent?: string;
  onAgentChange?: (agent: string) => void;
  selectedConversationId: string | null;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  threadId: string;
  setThreadId: (id: string) => void;
}

export function ChatInterface({ 
  selectedAgent, 
  onAgentChange, 
  selectedConversationId,
  messages: propsMessages,
  setMessages: propsSetMessages,
  isLoading,
  setIsLoading,
  threadId,
  setThreadId
}: ChatInterfaceProps) {
    const [input, setInput] = useState("");
    const [promptSuggestions, setPromptSuggestions] = useState<string[]>([]);

    const viewportRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const loadConversationMessages = async (conversationId: string | null) => {
            if (!conversationId) return;
            
            setIsLoading(true);
            try {
                const response = await fetch(`/api/history/${conversationId}`);
                const data = await response.json();
                console.log('Fetched conversation data:', data);
                
                const rawMessages = Array.isArray(data.messages) ? data.messages : [];
                const mappedMessages = rawMessages
                  .filter((msg: any) => msg.content && msg.content.trim() !== '')
                  .map((msg: any) => {
                    const baseMessage = {
                      role: msg.type === 'human' ? 'user' : 'assistant',
                      content: msg.type === 'tool' 
                        ? `Tool output: ${typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content, null, 2)}`
                        : msg.content,
                      id: msg.id || crypto.randomUUID(),
                      original: msg // Preserve original message for debugging
                    };
                    
                    if (msg.type === 'tool') {
                      return { ...baseMessage, tool: true };
                    }
                    return baseMessage;
                  });
                
                propsSetMessages(mappedMessages);
                setThreadId(data.thread_id);
                console.log('Mapped messages:', mappedMessages);
            } catch (error) {
                console.error('Failed to load conversation:', error);
            } finally {
                setIsLoading(false);
            }
        };

        loadConversationMessages(selectedConversationId);
    }, [selectedConversationId]);

    useEffect(() => {
        if (viewportRef.current) {
            viewportRef.current.scrollTo({ top: viewportRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [propsMessages, isLoading]);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !selectedAgent) return;

        const userMessage: Message = { role: 'user', content: input };
        // Add user message and an empty assistant message for the stream
        const assistantMessage: Message = { role: 'assistant', content: '' };
        propsSetMessages((prevMessages) => [...prevMessages, userMessage, assistantMessage]);
        setInput("");
        setIsLoading(true);
        setPromptSuggestions([]);

        try {
            await chatWithAgent(selectedAgent, input, (chunk) => {
                propsSetMessages(prev => {
                    const lastMessage = prev[prev.length - 1];
                    if (lastMessage.role === 'assistant') {
                        // Append the chunk to the last assistant message
                        const updatedLastMessage = { ...lastMessage, content: lastMessage.content + chunk };
                        return [...prev.slice(0, -1), updatedLastMessage];
                    }
                    return prev;
                });
            }, threadId); // Pass the current threadId to chatWithAgent
        } catch (error) {
            console.error(error);
            propsSetMessages(prev => {
                const lastMessage = prev[prev.length - 1];
                if (lastMessage.role === 'assistant' && lastMessage.content === '') {
                    // If the placeholder is empty, replace it with an error message
                    const errorMessage: Message = { role: 'assistant', content: "Sorry, I ran into an error. Please try again." };
                    return [...prev.slice(0, -1), errorMessage];
                }
                // Otherwise, add a new error message
                const errorMessage: Message = { role: 'assistant', content: "Sorry, I ran into an error. Please try again." };
                return [...prev, errorMessage];
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-full">
            <Card className="flex-1 flex flex-col shadow-lg rounded-xl">
                <CardContent className="flex-1 p-0 overflow-hidden">
                    <div className="h-full overflow-y-auto p-6 space-y-4" ref={viewportRef}>
                        {propsMessages.length === 0 && !isLoading && (
                            <div className="flex flex-col items-center justify-center h-full text-center">
                                <RediLogo className="h-16 w-16 text-primary mb-4" />
                                <h2 className="text-2xl font-semibold text-foreground">How can I help you today?</h2>
                                {promptSuggestions.length > 0 && (
                                  <div className="w-full flex flex-col sm:flex-row sm:flex-wrap gap-4 mt-8 max-w-3xl">
                                      {promptSuggestions.map((prompt, i) => (
                                          <PromptSuggestion key={i} prompt={prompt} onSelect={(p) => setInput(p)} />
                                      ))}
                                  </div>
                                )}
                            </div>
                        )}
                        {(() => { console.log('Rendering messages:', propsMessages); return null; })()}  
                        {propsMessages.map((message, index) => (
                            <ChatMessage 
                                key={`message-${index}`} 
                                message={message} 
                            />
                        ))}
                        {isLoading && (
                           <div className="flex items-start gap-4 animate-in fade-in">
                                <RediLogo className="h-8 w-8 shrink-0 text-primary"/>
                                <div className="flex items-center space-x-2 rounded-lg bg-card p-3 text-sm">
                                    <LoaderCircle className="h-5 w-5 animate-spin text-primary" />
                                    <span className="text-muted-foreground">Redi is thinking...</span>
                                </div>
                            </div>
                        )}
                    </div>
                </CardContent>
                <CardFooter className="p-4 border-t bg-card rounded-b-xl">
                    <form onSubmit={handleSubmit} className="flex w-full items-start space-x-2">
                        <Textarea
                            placeholder="Type your message here..."
                            className="min-h-12 resize-none"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e);
                                }
                            }}
                            disabled={isLoading || !selectedAgent}
                        />
                        <Button type="submit" size="icon" disabled={isLoading || !input.trim() || !selectedAgent}>
                            <Send className="h-4 w-4" />
                            <span className="sr-only">Send</span>
                        </Button>
                    </form>
                </CardFooter>
            </Card>
        </div>
    );
}
