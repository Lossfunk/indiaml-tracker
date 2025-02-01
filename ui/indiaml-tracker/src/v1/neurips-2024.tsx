import { ResearchPapersShowcase } from "./research-paper-showcase";

export default function Home() {
    return (
      <main className="container mx-auto p-4">
        <div className="max-w-[700px] text-center">
        <h1 className="text-xl font-bold mb-8 text-center">Indian Research Papers accepted at Top AI/ML conferences in 2024!</h1>
        <h6 className="text-base">
          These are the papers that were accepted where at least one author could be verified to have done their research from an Indian Institude or Research Unit.
        </h6>

        </div>
        <ResearchPapersShowcase />
      </main>
    )
  }
  
  