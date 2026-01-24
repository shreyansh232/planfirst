"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChatInterface } from "@/components/chat/ChatInterface";

export default function PlanPage() {
  const [started, setStarted] = useState(false);
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    if (origin && destination) {
      setStarted(true);
    }
  };

  if (!started) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-8">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle className="text-2xl">Plan Your Trip</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleStart} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Where are you traveling from?</label>
                <Input
                  placeholder="e.g., Mumbai, New York, London"
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Where do you want to go?</label>
                <Input
                  placeholder="e.g., San Francisco, Tokyo, Paris"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" size="lg">
                Start Planning
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      <ChatInterface origin={origin} destination={destination} />
    </div>
  );
}
