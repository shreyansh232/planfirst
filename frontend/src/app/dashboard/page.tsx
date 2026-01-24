"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  // TODO: Fetch user's trips from API
  const trips: { id: string; origin: string; destination: string; createdAt: string }[] = [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Your Trips</h1>
            <p className="text-slate-400">Manage your travel plans</p>
          </div>
          <Link href="/plan">
            <Button size="lg">Plan New Trip</Button>
          </Link>
        </div>

        {trips.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <div className="text-6xl mb-4">🌍</div>
              <h2 className="text-xl font-semibold mb-2">No trips yet</h2>
              <p className="text-muted-foreground mb-4">
                Start planning your first adventure!
              </p>
              <Link href="/plan">
                <Button>Plan Your First Trip</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {trips.map((trip) => (
              <Card key={trip.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle>{trip.destination}</CardTitle>
                  <CardDescription>From {trip.origin}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Created {new Date(trip.createdAt).toLocaleDateString()}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
