import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { Paper } from "@/types/paper"

interface PaperCardProps {
  paper: Paper
}

export function PaperCard({ paper }: PaperCardProps) {
  return (
    <Card className="h-full flex flex-col overflow-hidden transition-shadow hover:shadow-md">
      <CardHeader className="bg-orange-50 border-b border-orange-100">
        <CardTitle className="text-lg text-gray-800">{paper.title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-grow flex flex-col justify-between p-4">
        <div>
          <p className="text-sm text-gray-600 mb-4">{paper.abstract}</p>
          <div className="flex flex-wrap gap-2 mb-4">
            <TooltipProvider>
              {paper.authors.map((author, index) => (
                <Tooltip key={index}>
                  <TooltipTrigger>
                    <Badge variant="secondary" className="bg-blue-50 text-blue-700">
                      {author}
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{getAuthorInfo(author)}</p>
                  </TooltipContent>
                </Tooltip>
              ))}
            </TooltipProvider>
          </div>
        </div>
        <div className="flex justify-between items-center">
          <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-200">{paper.conference}</Badge>
          <span className="text-sm text-gray-500">{paper.year}</span>
        </div>
      </CardContent>
    </Card>
  )
}

function getAuthorInfo(author: string): string {
  // This is a placeholder function. In a real application, you would fetch this information from a database or API.
  const institutions = [
    "Indian Institute of Technology",
    "Indian Statistical Institute",
    "Tata Institute of Fundamental Research",
    "Indian Institute of Science",
  ]
  const randomInstitution = institutions[Math.floor(Math.random() * institutions.length)]
  return `${author}\nAffiliation: ${randomInstitution}`
}

