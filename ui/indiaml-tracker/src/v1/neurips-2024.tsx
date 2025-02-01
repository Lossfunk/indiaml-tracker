import { ResearchPapersShowcase } from "./research-paper-showcase";

export default function Home() {
    return (
      <main className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-8 text-center">Indian Research Papers at NeurIPS and ICML 2024</h1>
        <ResearchPapersShowcase />
      </main>
    )
  }
  
  