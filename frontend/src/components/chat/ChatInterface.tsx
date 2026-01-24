"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  phase?: string;
  searchQueries?: string[];
}

interface ChatInterfaceProps {
  origin: string;
  destination: string;
}

const PHASE_LABELS: Record<string, string> = {
  clarification: "Phase 1: Clarification",
  feasibility: "Phase 2: Feasibility Check",
  assumptions: "Phase 3: Assumptions",
  planning: "Phase 4: Plan Generation",
  refinement: "Phase 5: Refinement",
};

export function ChatInterface({ origin, destination }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentPhase, setCurrentPhase] = useState("clarification");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Start conversation when component mounts
  useEffect(() => {
    const startConversation = async () => {
      setIsLoading(true);
      // TODO: Call API to start conversation with origin/destination
      // For now, show a placeholder message
      const initialMessage: Message = {
        id: "1",
        role: "assistant",
        content: `Great! I'll help you plan your trip from ${origin} to ${destination}.\n\nBefore I create your itinerary, I need to understand your constraints:\n\n1. What month or season are you planning to travel?\n2. How many total days (including travel)?\n3. Solo or group travel?\n4. What's your budget level (budget/mid-range/luxury or specific amount)?\n5. Comfort with rough conditions (low/medium/high)?`,
        phase: "clarification",
      };
      setMessages([initialMessage]);
      setIsLoading(false);
    };

    startConversation();
  }, [origin, destination]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // TODO: Implement actual streaming from backend
      // For now, simulate a response
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "This is a placeholder response. Connect to the backend API to get real responses.",
        phase: currentPhase,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">
              {origin} → {destination}
            </h1>
            <p className="text-sm text-slate-400">
              {PHASE_LABELS[currentPhase] || currentPhase}
            </p>
          </div>
          <div className="flex gap-2">
            {Object.entries(PHASE_LABELS).map(([key, label], index) => (
              <div
                key={key}
                className={`w-3 h-3 rounded-full ${
                  key === currentPhase
                    ? "bg-blue-500"
                    : index < Object.keys(PHASE_LABELS).indexOf(currentPhase)
                    ? "bg-green-500"
                    : "bg-slate-600"
                }`}
                title={label}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <Card
                className={`max-w-[80%] p-4 ${
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-slate-700 text-slate-100"
                }`}
              >
                {message.searchQueries && message.searchQueries.length > 0 && (
                  <div className="mb-2 text-xs text-slate-400">
                    {message.searchQueries.map((query, i) => (
                      <div key={i}>🔍 Searching: {query}</div>
                    ))}
                  </div>
                )}
                <div className="whitespace-pre-wrap">{message.content}</div>
              </Card>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <Card className="bg-slate-700 p-4">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                  <div
                    className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  />
                  <div
                    className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  />
                </div>
              </Card>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-slate-800 border-t border-slate-700 p-4">
        <form
          onSubmit={handleSubmit}
          className="max-w-4xl mx-auto flex gap-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your response..."
            className="flex-1 bg-slate-700 border-slate-600 text-white"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
