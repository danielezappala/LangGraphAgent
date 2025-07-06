"use client";

import { useState, useRef, useEffect, FormEvent } from 'react';
import { AgentsMenu } from '@/components/agents-menu';
import { chatWithAgent } from '@/app/api/agents';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, LoaderCircle } from "lucide-react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { RediLogo } from '@/components/icons';
import { HistoryModal } from '@/components/history-modal';
import { getAiResponse } from '@/app/actions';
import { ChatMessage, type Message } from '@/components/chat-message';
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
}

export function ChatInterface({ selectedAgent, onAgentChange }: ChatInterfaceProps) {
    const [showHistory, setShowHistory] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [promptSuggestions, setPromptSuggestions] = useState<string[]>([]);

    const viewportRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const getSuggestions = async () => {
            try {
                const suggestions = await Promise.all([
                    generatePromptStarter({}),
                    generatePromptStarter({}),
                ]);
                setPromptSuggestions(suggestions.map(s => s.prompt));
            } catch (error) {
                console.error("Failed to generate prompt starters:", error);
            }
        }
        getSuggestions();
    }, []);

    useEffect(() => {
        if (viewportRef.current) {
            viewportRef.current.scrollTo({ top: viewportRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [messages, isLoading]);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !selectedAgent) return;

        const userMessage: Message = { role: 'user', content: input };
        const newMessages = [...messages, userMessage];
        setMessages(newMessages);
        setInput("");
        setIsLoading(true);
        setPromptSuggestions([]);

        try {
            const aiResponse = await chatWithAgent(selectedAgent, input);
            setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);
        } catch (error) {
            console.error(error);
            const errorMessage: Message = { role: 'assistant', content: "Sorry, I ran into an error. Please try again." };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-full">
            {/* Pulsante History in alto */}
            {selectedAgent && (
                <div className="flex justify-end mb-2">
                    <Button variant="outline" size="sm" onClick={() => setShowHistory(true)}>
                        Cronologia
                    </Button>
                </div>
            )}
            <HistoryModal agentId={selectedAgent || ''} open={showHistory} onOpenChange={setShowHistory} />
            <Card className="flex-1 flex flex-col shadow-lg rounded-xl">
                <CardContent className="flex-1 p-0 overflow-hidden">
                    <div className="h-full overflow-y-auto p-6 space-y-4" ref={viewportRef}>
                        {messages.length === 0 && !isLoading && (
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
                        {messages.map((msg, index) => <ChatMessage key={index} message={msg} />)}
                        {isLoading && (
                           <div className="flex items-start gap-4 animate-in fade-in">
                                <RediLogo className="h-8 w-8 shrink-0 text-primary"/>
                                <div className="flex items-center space-x-2 rounded-lg bg-card p-3 text-sm">
                                    <LoaderCircle className="h-5 w-5 animate-spin text-primary" />
                                    <span className="text-muted-foreground">AquaChat is thinking...</span>
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
