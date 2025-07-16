"use client";

import { useState, useRef, useEffect, FormEvent } from 'react';
import { AgentsMenu } from '@/components/agents-menu';
import { chatWithAgent } from '@/app/api/agents';
import { generateId } from '@/lib/utils';
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
    onConversationUpdate?: () => Promise<void>;
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
    setThreadId,
    onConversationUpdate
}: ChatInterfaceProps) {
    const [input, setInput] = useState("");
    const [promptSuggestions, setPromptSuggestions] = useState<string[]>([]);

    const viewportRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (viewportRef.current) {
            viewportRef.current.scrollTo({ top: viewportRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [propsMessages, isLoading]);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !selectedAgent) return;

        const userMessage: Message = { role: 'user', content: input, id: generateId() };
        propsSetMessages((prevMessages) => [...prevMessages, userMessage]);
        setInput("");
        setIsLoading(true);
        setPromptSuggestions([]);

        try {
            await chatWithAgent(selectedAgent, input, (rawChunk) => {
                if (!rawChunk) return;
                try {
                    const parsedData = JSON.parse(rawChunk);
                    // Handle both direct and nested message formats
                    const messageData = parsedData.message || parsedData;

                    if (!messageData || !messageData.type) {
                        console.warn("Received chunk without valid message data:", parsedData);
                        return;
                    }

                    propsSetMessages(prev => {
                        let newMessages = [...prev];

                        let lastMessage = newMessages.length > 0 ? newMessages[newMessages.length - 1] : null;
                        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.content === '') {
                            newMessages.pop();
                        }

                        lastMessage = newMessages.length > 0 ? newMessages[newMessages.length - 1] : null;

                        if (messageData.type === "tool_result") {
                            // Only add the tool message if there's content
                            if (messageData.content) {
                                newMessages.push({
                                    role: 'assistant',
                                    tool: true,
                                    tool_name: messageData.tool_name,
                                    content: messageData.content,
                                    id: messageData.id || crypto.randomUUID()
                                });
                            }

                        } else if (messageData.type === "text") {
                            // Skip empty content chunks
                            if (!messageData.content) {
                                return newMessages;
                            }

                            // If the last message is an assistant message, append to it
                            if (lastMessage && lastMessage.role === 'assistant' && !lastMessage.tool) {
                                lastMessage.content = (lastMessage.content || '') + messageData.content;
                                lastMessage.id = messageData.id || lastMessage.id || crypto.randomUUID();
                            } else {
                                // Otherwise, create a new message
                                newMessages.push({
                                    role: 'assistant',
                                    content: messageData.content,
                                    id: messageData.id || crypto.randomUUID(),
                                });
                            }

                        } else if (messageData.type === "error") {
                            newMessages.push({
                                role: 'assistant',
                                content: `Error: ${messageData.content}`,
                                id: messageData.id || crypto.randomUUID()
                            });

                        } else if (messageData.type === "end") {
                            console.log("Stream ended by 'end' chunk.");
                        }

                        return newMessages;
                    });

                } catch (e) {
                    console.error("ChatInterface: Failed to parse or process stream chunk:", rawChunk, e);
                }
            }, threadId);
        } catch (error) {
            console.error("ChatInterface: Error in handleSubmit call to chatWithAgent", error);
            propsSetMessages(prev => {
                const newMessages = [...prev];
                if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'assistant' && newMessages[newMessages.length - 1].content === '') {
                    newMessages.pop();
                }
                newMessages.push({ role: 'assistant', content: "Sorry, an error occurred while connecting to the agent.", id: crypto.randomUUID() });
                return newMessages;
            });
        } finally {
            setIsLoading(false);
            // Refresh conversations list after sending a message
            if (onConversationUpdate) {
                try {
                    await onConversationUpdate();
                } catch (error) {
                    console.error("Failed to refresh conversations:", error);
                }
            }
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
                                <RediLogo className="h-8 w-8 shrink-0 text-primary" />
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
