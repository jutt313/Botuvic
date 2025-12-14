import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

export default function SettingsPage() {
  const [searchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'general'

  return (
    <div className="min-h-screen bg-background">
      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8 animate-fade-in">Settings</h1>
        <div className="bg-surface rounded-lg border border-muted p-6 animate-slide-up">
          {tab === 'llm' ? (
            <div>
              <h2 className="text-xl font-semibold mb-4">LLM Configuration</h2>
              <p className="text-muted">LLM settings coming soon...</p>
            </div>
          ) : (
            <p className="text-muted">Settings page coming soon...</p>
          )}
        </div>
      </main>
    </div>
  )
}

