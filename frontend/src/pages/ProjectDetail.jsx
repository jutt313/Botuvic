import { useParams } from 'react-router-dom'

export default function ProjectDetailPage() {
  const { id } = useParams()

  return (
    <div className="min-h-screen bg-background">
      <main className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8 animate-fade-in">
          Project: {id}
        </h1>
        <div className="bg-surface rounded-lg border border-muted p-6 animate-slide-up">
          <p className="text-muted">Project detail page coming soon...</p>
        </div>
      </main>
    </div>
  )
}

