import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

export default function SettingsPage() {
  const [searchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'general'

  return (
    <div className="min-h-screen" style={{ 
      background: 'linear-gradient(to top, #000000 0%, #000000 35%, #05020A 45%, #0A0514 55%, #0F0819 65%, #140B1F 75%, #1A0F2E 85%, #1A0F2E 100%)',
      backgroundAttachment: 'fixed'
    }}>
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

